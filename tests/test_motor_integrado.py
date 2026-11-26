import json
import threading
import time
import unittest
import urllib.request
from unittest.mock import Mock

from coach.motor import Motor
from coach.gsi.server import ServidorGSI
from coach.prioridades import ControlAvisos
from coach.eventos import Evento
from coach.state import parsear


def payload(vida=100, mana=100, vivo=True, muertes=0, pausa=False, partida='1', reloj=100, fase='DOTA_GAMERULES_STATE_GAME_IN_PROGRESS'):
    return {'map': {'matchid': partida, 'paused': pausa, 'clock_time': reloj, 'game_state': fase},
            'hero': {'name':'npc_dota_hero_pudge', 'level':6, 'alive':vivo,
                     'health_percent':vida, 'mana_percent':mana},
            'player': {'deaths':muertes}}


class Salida:
    def __init__(self):
        self.avisos = []
    def configurar(self, *args): pass
    def estado(self, texto): pass
    def mostrar(self, texto, vigente=None): self.avisos.append((texto, vigente))
    hablar = mostrar


class Proveedor:
    def __init__(self):
        self.inicio = threading.Event()
        self.liberar = threading.Event()
        self.prompts = []
        self.activo = True
    def disponible(self): return self.activo
    def generar(self, prompt):
        self.prompts.append(prompt)
        self.inicio.set()
        if not self.liberar.wait(3): raise RuntimeError('Prueba agotada')
        return '**Evalúa tu posición antes de regresar.**'


class TestMotorIntegrado(unittest.TestCase):
    def setUp(self):
        self.t = 0
        self.ui, self.voz, self.prov = Salida(), Salida(), Proveedor()
        self.cfg = {'voz':True, 'persona':'profesional'}
        self.motor = Motor(self.cfg, self.prov, self.voz, self.ui, reloj=lambda:self.t)
        self.addCleanup(self.limpiar)

    def limpiar(self):
        self.motor.cerrar()
        self.prov.liberar.set()
        self.esperar_ia()

    def esperar_ia(self):
        limite = time.monotonic()+2
        while self.motor._ia_ocupada and time.monotonic()<limite:
            time.sleep(.005)
        self.assertFalse(self.motor._ia_ocupada)

    def enviar(self, t, **kw):
        self.t = t
        self.motor.procesar(payload(**kw))

    def habilitar(self):
        self.enviar(0)
        self.assertTrue(self.motor.habilitar_practica())

    def muerte(self):
        self.habilitar()
        self.enviar(1, vivo=False, muertes=1, vida=0)
        self.assertTrue(self.prov.inicio.wait(1))

    def test_silencio_por_defecto(self):
        self.enviar(0)
        self.enviar(1, vida=15)
        self.assertFalse(self.ui.avisos or self.voz.avisos or self.prov.prompts)

    def test_sin_ia_aviso_local_y_vigencia(self):
        self.prov.activo = False
        self.habilitar()
        self.enviar(1, vida=15, mana=10)
        self.assertEqual(len(self.voz.avisos), 1)
        texto, guardia = self.voz.avisos[0]
        self.assertIn('vida', texto)
        self.assertTrue(guardia())
        self.enviar(2, vida=90)
        self.assertFalse(guardia())
        self.assertFalse(self.prov.prompts)

    def test_modo_competitivo_y_cierre(self):
        self.enviar(0)
        self.cfg['modo_competitivo'] = True
        self.motor.aplicar_config()
        self.assertFalse(self.motor.habilitar_practica())
        self.motor.cerrar()
        self.assertFalse(self.motor.habilitar_practica())

    def test_nueva_partida_no_hereda_permiso(self):
        self.habilitar()
        self.enviar(1, partida='2')
        self.enviar(2, partida='2', vida=10)
        self.assertFalse(self.voz.avisos)

    def test_reconexion_no_hereda_permiso(self):
        self.habilitar()
        self.enviar(4, vida=10)
        self.assertFalse(self.voz.avisos)

    def test_ia_entrega_limpia_y_sin_identificadores(self):
        self.muerte()
        self.enviar(2, vivo=False, muertes=1, vida=0)
        self.prov.liberar.set()
        self.esperar_ia()
        self.assertEqual(len(self.voz.avisos), 1)
        self.assertNotIn('*', self.voz.avisos[0][0])
        self.assertNotIn('matchid', self.prov.prompts[0])
        self.assertTrue(self.voz.avisos[0][1]())

    def test_ia_descartada_por_caducidad(self):
        self.muerte()
        for t in range(2,11):
            self.enviar(t, vivo=False, muertes=1, vida=0)
        self.prov.liberar.set()
        self.esperar_ia()
        self.assertFalse(self.voz.avisos)

    def test_ia_descartada_por_pausa_aunque_se_reanude(self):
        self.muerte()
        self.enviar(2, vivo=False, muertes=1, vida=0, pausa=True)
        self.enviar(3, vivo=False, muertes=1, vida=0)
        self.prov.liberar.set()
        self.esperar_ia()
        self.assertFalse(self.voz.avisos)

    def test_ia_descartada_por_reaparicion(self):
        self.muerte()
        self.enviar(2, vivo=True, muertes=1)
        self.prov.liberar.set()
        self.esperar_ia()
        self.assertFalse(self.voz.avisos)

    def test_ia_descartada_por_detener(self):
        self.muerte()
        self.motor.deshabilitar_practica()
        self.prov.liberar.set()
        self.esperar_ia()
        self.assertFalse(self.voz.avisos)

    def test_guardia_expira_sin_post(self):
        self.habilitar()
        self.enviar(1, vida=10)
        guardia = self.voz.avisos[0][1]
        self.t = 5
        self.assertFalse(guardia())

    def test_http_responde_con_ia_bloqueada(self):
        self.muerte()
        servidor = ServidorGSI(0, [self.motor.procesar])
        servidor.iniciar_en_hilo()
        try:
            self.t = 2
            req = urllib.request.Request('http://127.0.0.1:%d/' % servidor.puerto,
                    data=json.dumps(payload(vivo=False, muertes=1, vida=0)).encode(), method='POST')
            with urllib.request.urlopen(req, timeout=2) as respuesta:
                self.assertEqual(respuesta.status, 200)
            self.assertTrue(self.motor._ia_ocupada)
            self.assertEqual(self.motor._ultimo_gsi, 2)
        finally:
            servidor.detener()

    def test_contador_muerte_antes_del_estado_no_bloquea_muerte_real(self):
        c = ControlAvisos()
        vivo = parsear(payload(muertes=1))
        muerto = parsear(payload(vivo=False, muertes=1))
        opciones = dict(practica=True, ia_disponible=True, ia_ocupada=False)
        self.assertIsNone(c.seleccionar([Evento('muerte', valor=1)], vivo, 0, **opciones))
        self.assertEqual(c.seleccionar([Evento('muerte', valor=1)], muerto, 1, **opciones).tipo, 'muerte')
