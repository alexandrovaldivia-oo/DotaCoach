import unittest
from unittest.mock import Mock, patch

from coach.motor import Motor, _VigenciaVoz
from coach.voice.tts import ReproductorVoz
from test_motor_integrado import payload, Salida


class TestContinuidadMotor(unittest.TestCase):
    def setUp(self):
        self.t = 0
        self.voz = Salida()
        self.cfg = {'voz': True}
        proveedor = Mock()
        proveedor.disponible.return_value = False
        self.motor = Motor(self.cfg, proveedor, self.voz, Salida(), reloj=lambda: self.t)
        self.addCleanup(self.motor.cerrar)
        self.enviar(0)
        self.assertTrue(self.motor.habilitar_practica())
        self.enviar(1, vida=15)
        self.guardia = self.voz.avisos[-1][1]

    def enviar(self, t, **kw):
        self.t = t
        self.motor.procesar(payload(**kw))

    def test_caducidad_solo_antes_de_hablar(self):
        for t in range(2, 12):
            self.enviar(t, vida=15)
        self.assertFalse(self.guardia())
        self.assertTrue(self.guardia.durante())

    def test_recuperacion_no_corta_audio(self):
        self.enviar(2, vida=100)
        self.assertFalse(self.guardia())
        self.assertTrue(self.guardia.durante())

    def test_detener(self):
        self.motor.deshabilitar_practica()
        self.assertFalse(self.guardia.durante())

    def test_pausa_y_reanudacion(self):
        self.enviar(2, pausa=True)
        self.enviar(3)
        self.assertFalse(self.guardia.durante())

    def test_muerte(self):
        self.enviar(2, vivo=False, vida=0, muertes=1)
        self.assertFalse(self.guardia.durante())

    def test_desconexion(self):
        self.t = 5
        self.assertFalse(self.guardia.durante())

    def test_nueva_partida(self):
        self.enviar(2, partida='2')
        self.assertFalse(self.guardia.durante())

    def test_voz_desactivada(self):
        self.cfg['voz'] = False
        self.assertFalse(self.guardia.durante())

    def test_competitivo(self):
        self.cfg['modo_competitivo'] = True
        self.motor.aplicar_config()
        self.assertFalse(self.guardia.durante())

    def test_cierre(self):
        self.motor.cerrar()
        self.assertFalse(self.guardia.durante())


class TestReproduccion(unittest.TestCase):
    def setUp(self):
        self.voz = ReproductorVoz.__new__(ReproductorVoz)
        self.voz.volumen = .9
        self.voz._sintetizar = Mock()
        self.voz._iniciar_mixer = Mock()
        self.musica = self.voz._iniciar_mixer.return_value.music
        self.musica.get_busy.side_effect = [True, True, False]

    @patch('coach.voice.tts.time.sleep')
    def test_audio_termina_con_admision_expirada(self, dormir):
        antes = Mock(side_effect=[True, True, True, False])
        durante = Mock(return_value=True)
        with self.assertLogs('coach.voz', level='INFO') as logs:
            self.voz._reproducir('Consejo', _VigenciaVoz(antes, durante))
        self.assertEqual(antes.call_count, 3)
        self.assertEqual(durante.call_count, 2)
        self.musica.stop.assert_not_called()
        self.musica.unload.assert_called_once()
        self.assertIn('reproduccion finalizada', ' '.join(logs.output))

    def test_audio_interrumpido_por_continuidad(self):
        with self.assertLogs('coach.voz', level='INFO') as logs:
            self.voz._reproducir('Consejo', _VigenciaVoz(lambda: True, lambda: False))
        self.musica.stop.assert_called_once()
        self.musica.unload.assert_called_once()
        self.assertIn('reproduccion interrumpida', ' '.join(logs.output))

    def test_audio_caducado_en_sintesis_no_comienza(self):
        antes = Mock(side_effect=[True, False])
        self.voz._reproducir('Consejo', _VigenciaVoz(antes, lambda: True))
        self.musica.play.assert_not_called()
        self.voz._iniciar_mixer.assert_not_called()

    def test_error_de_audio_libera_recursos(self):
        self.musica.get_busy.side_effect = RuntimeError('error simulado')
        with self.assertLogs('coach.voz', level='WARNING'):
            self.voz._reproducir('Consejo', None)
        self.musica.stop.assert_called_once()
        self.musica.unload.assert_called_once()
