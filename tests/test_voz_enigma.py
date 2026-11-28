import base64
import unittest
from coach.draft.voz_enigma import limpiar, interpretar_audio, respuesta_contextual, AudioWindows, PERSONALIDADES
from unittest.mock import patch

class VozEnigmaTest(unittest.TestCase):
    def test_limpieza(self):
        self.assertEqual(limpiar('**Hola** #jefe 😃 https://ejemplo.com'), 'Hola jefe')
    def test_transcripcion(self):
        self.assertEqual(interpretar_audio('OK:'+base64.b64encode('Soy posición dos'.encode()).decode()),'Soy posición dos')
    def test_baja_confianza(self):
        with self.assertRaises(RuntimeError): interpretar_audio('BAJA')
    def test_sin_reconocedor(self):
        with self.assertRaisesRegex(RuntimeError,'español'): interpretar_audio('NO_ES')
    def test_datos_invalidos(self):
        with self.assertRaises(RuntimeError): interpretar_audio('OK:%%%')
    def test_contexto(self):
        self.assertIn('Aliados: Lion',respuesta_contextual('Indica candidatos disponibles para el estudio','Aliados: Lion'))
    def test_personalidades(self):
        for p in PERSONALIDADES:
            self.assertTrue(respuesta_contextual('Información insuficiente.','',p).endswith('Información insuficiente.'))
    def test_humor_opcional(self):
        t='Información insuficiente. No se emite una recomendación competitiva.'
        self.assertNotIn('bola de cristal',respuesta_contextual(t,''))
        self.assertIn('bola de cristal',respuesta_contextual(t,'',sarcasmo=True))
    def test_ticket(self):
        a=AudioWindows(); t=a.ticket(); a.cancelar(); self.assertNotEqual(t,a.ticket())
    def test_audio_mock(self):
        a=AudioWindows()
        with patch.object(a,'_ejecutar',return_value='OK') as f:
            a.hablar('**Hola**',0)
            self.assertEqual(base64.b64decode(f.call_args.args[1]),b'Hola')
