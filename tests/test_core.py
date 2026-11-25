import json
import os
import sys
import time
import unittest
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coach.state import parsear, EstadoPartida
from coach.eventos import detectar
from coach.reglas import consejos_por_tiempo, consejos_por_evento
from coach.texto import limpiar_texto
from coach.gsi.server import ServidorGSI
from coach.gsi.setup import contenido_cfg, HOST
from coach.persona import construir_prompt


def payload(reloj=100, nivel=3, oro=500, kills=0, deaths=0, racha=0, items=None, matchid="1"):
    items = items or {}
    bloque_items = {"slot%d" % i: {"name": "empty"} for i in range(9)}
    for i, nombre in enumerate(items):
        bloque_items["slot%d" % i] = {"name": nombre}
    return {
        "map": {"clock_time": reloj, "matchid": matchid, "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"},
        "hero": {"name": "npc_dota_hero_juggernaut", "level": nivel, "alive": True},
        "player": {"gold": oro, "kills": kills, "deaths": deaths, "assists": 0, "kill_streak": racha},
        "items": bloque_items,
        "abilities": {"ability0": {"name": "juggernaut_blade_fury", "level": 1}},
    }


class PruebasEstado(unittest.TestCase):
    def test_parsea_campos(self):
        e = parsear(payload(reloj=125, nivel=4, oro=800, items=["item_blink"]))
        self.assertTrue(e.en_partida)
        self.assertEqual(e.heroe, "juggernaut")
        self.assertEqual(e.minuto, 2)
        self.assertEqual(e.items, frozenset({"item_blink"}))
        self.assertEqual(e.habilidades, (("juggernaut_blade_fury", 1),))

    def test_datos_vacios_o_invalidos(self):
        self.assertFalse(parsear({}).en_partida)
        self.assertFalse(parsear(None).en_partida)
        self.assertFalse(parsear({"provider": {"name": "Dota 2"}}).en_partida)
        self.assertEqual(parsear({"hero": {"level": "x"}, "map": {"clock_time": None}}).reloj, 0)


class PruebasEventos(unittest.TestCase):
    def test_inicio_de_partida(self):
        ev = detectar(EstadoPartida(), parsear(payload()))
        self.assertEqual([e.tipo for e in ev], ["inicio"])

    def test_nivel_item_muerte_racha(self):
        a = parsear(payload(reloj=300, nivel=5))
        b = parsear(payload(reloj=310, nivel=6, deaths=1, racha=3, items=["item_blink"]))
        tipos = [e.tipo for e in detectar(a, b)]
        self.assertEqual(sorted(tipos), ["item_nuevo", "muerte", "nivel", "racha"])

    def test_items_iniciales_antes_de_la_bocina_no_cuentan(self):
        a = parsear(payload(reloj=-30))
        b = parsear(payload(reloj=-20, items=["item_tango"]))
        self.assertEqual(detectar(a, b), [])

    def test_partida_nueva_reinicia(self):
        a = parsear(payload(matchid="1", reloj=900))
        b = parsear(payload(matchid="2", reloj=5))
        self.assertEqual([e.tipo for e in detectar(a, b)], ["inicio"])


class PruebasReglas(unittest.TestCase):
    def test_runa_de_sabiduria(self):
        textos = [c.texto for c in consejos_por_tiempo(6 * 60 + 25, 6 * 60 + 35)]
        self.assertEqual(len(textos), 1)
        self.assertIn("sabiduría", textos[0].lower())

    def test_sin_aviso_si_el_reloj_no_avanza(self):
        self.assertEqual(consejos_por_tiempo(500, 500), [])

    def test_definitiva_solo_en_6_12_18(self):
        e6 = parsear(payload(nivel=6))
        from coach.eventos import Evento
        self.assertEqual(len(consejos_por_evento(Evento("nivel", valor=6), e6)), 1)
        self.assertEqual(consejos_por_evento(Evento("nivel", valor=5), e6), [])


class PruebasTexto(unittest.TestCase):
    def test_limpia_simbolos_y_emojis(self):
        self.assertEqual(limpiar_texto("**Hola** m**** _jefe_ \U0001F525"), "Hola m jefe")

    def test_prompt_incluye_reglas(self):
        p = construir_prompt("peon", parsear(payload()), "Acabo de morir.", [], 22)
        self.assertIn("Prohibido usar asteriscos", p)
        self.assertIn("Acabo de morir.", p)


class PruebasServidor(unittest.TestCase):
    def test_recibe_post(self):
        recibidos = []
        servidor = ServidorGSI(0, [recibidos.append])
        servidor.iniciar_en_hilo()
        try:
            req = urllib.request.Request(
                "http://%s:%d/" % (HOST, servidor.puerto),
                data=json.dumps(payload()).encode("utf-8"), method="POST")
            self.assertEqual(urllib.request.urlopen(req, timeout=3).status, 200)
            time.sleep(0.1)
        finally:
            servidor.detener()
        self.assertEqual(len(recibidos), 1)
        self.assertEqual(recibidos[0]["hero"]["level"], 3)

    def test_cfg_contiene_componentes(self):
        base = contenido_cfg(4125)
        completo = contenido_cfg(4125, completo=True)
        self.assertIn('"events"', base)
        self.assertNotIn('"buildings"', base)
        self.assertIn('"buildings"', completo)
        self.assertIn(":4125/", base)


if __name__ == "__main__":
    unittest.main()


class FalsaUI:
    def __init__(self):
        self.mensajes = []
        self.estados = []

    def mostrar(self, texto):
        self.mensajes.append(texto)

    def estado(self, texto):
        self.estados.append(texto)


class FalsaVoz:
    def __init__(self):
        self.dichos = []

    def configurar(self, *args, **kwargs):
        pass

    def hablar(self, texto):
        self.dichos.append(texto)


class FalsoProveedor:
    def __init__(self, respuesta="Juega mas atras, ** hermano."):
        self.respuesta = respuesta
        self.prompts = []

    def disponible(self):
        return True

    def generar(self, prompt, imagen_jpeg=None):
        self.prompts.append(prompt)
        return self.respuesta


class PruebasMotor(unittest.TestCase):
    def _motor(self, **cfg_extra):
        from coach.motor import Motor
        cfg = {"persona": "profesional", "voz": True, "cooldown_ia": 0, "max_palabras": 22}
        cfg.update(cfg_extra)
        ui, voz, prov = FalsaUI(), FalsaVoz(), FalsoProveedor()
        return Motor(cfg, prov, voz, ui), ui, voz, prov

    def test_muerte_pide_consejo_a_la_ia_y_limpia_el_texto(self):
        motor, ui, voz, prov = self._motor()
        motor.procesar(payload(reloj=300, deaths=0))
        motor._ultimo_aviso = 0
        motor.procesar(payload(reloj=310, deaths=1))
        for _ in range(50):
            if voz.dichos:
                break
            time.sleep(0.05)
        self.assertEqual(len(prov.prompts), 1)
        self.assertIn("Acabo de morir", prov.prompts[0])
        self.assertTrue(voz.dichos)
        self.assertNotIn("*", voz.dichos[-1])

    def test_modo_competitivo_no_aconseja(self):
        motor, ui, voz, prov = self._motor(modo_competitivo=True)
        motor.procesar(payload(reloj=300))
        motor.procesar(payload(reloj=310, deaths=1, nivel=6))
        time.sleep(0.2)
        self.assertEqual(voz.dichos, [])
        self.assertEqual(prov.prompts, [])

    def test_aviso_de_runa_sin_ia(self):
        motor, ui, voz, prov = self._motor()
        motor.procesar(payload(reloj=389))
        motor._ultimo_aviso = 0
        motor.procesar(payload(reloj=391))
        self.assertTrue(any("sabiduría" in d for d in voz.dichos))
        self.assertEqual(prov.prompts, [])
