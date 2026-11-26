import json
import unittest
from coach.simulador import reproducir


def linea(t, racha=0, pausa=False, vivo=True, match='privado'):
    return json.dumps({'t': t, 'datos': {'map': {'matchid': match, 'paused': pausa,
        'clock_time': int(t), 'game_state': 'DOTA_GAMERULES_STATE_GAME_IN_PROGRESS'},
        'hero': {'name': 'npc_dota_hero_pudge', 'alive': vivo, 'level': 2},
        'player': {'kill_streak': racha, 'steamid': 'secreto'}}})


class TestSimulador(unittest.TestCase):
    def test_vacio(self):
        self.assertEqual(reproducir(['\n']).mensajes, 0)

    def test_bloqueo_por_defecto(self):
        r = reproducir([linea(0), linea(1, 3), linea(3, 3)])
        self.assertEqual(r.eventos['racha'], 1)
        self.assertEqual(r.solicitudes, 0)

    def test_respuesta_y_privacidad(self):
        datos = [linea(0), linea(1, 3), linea(3, 3)]
        r = reproducir(datos, practica=True)
        self.assertEqual((r.solicitudes, r.respuestas_aceptadas), (1, 1))
        self.assertNotIn('privado', json.dumps(r.publico()))
        self.assertNotIn('secreto', json.dumps(r.publico()))
        self.assertEqual(r.publico(), reproducir(datos, practica=True).publico())

    def test_pausa_simultanea(self):
        r = reproducir([linea(0), linea(1, 3), linea(3, 3, pausa=True)], practica=True)
        self.assertEqual(r.respuestas_descartadas, 1)

    def test_caducidad(self):
        r = reproducir([linea(0), linea(1, 3), linea(11, 3)], practica=True, demora=9)
        self.assertEqual(r.respuestas_descartadas, 1)

    def test_desconexion(self):
        r = reproducir([linea(0), linea(1, 3), linea(10, 3)], practica=True, demora=4)
        self.assertEqual(r.respuestas_descartadas, 1)

    def test_pendiente(self):
        r = reproducir([linea(0), linea(1, 3)], practica=True)
        self.assertEqual(r.pendientes_al_final, 1)

    def test_demora_cero(self):
        r = reproducir([linea(0), linea(1, 3)], practica=True, demora=0)
        self.assertEqual(r.respuestas_aceptadas, 1)

    def test_registros_invalidos(self):
        for datos in (['{'], ['{}'], [linea(2), linea(1)], ['{"t":NaN,"datos":{}}']):
            with self.assertRaises(ValueError):
                reproducir(datos)

    def test_filtro_respuesta(self):
        r = reproducir([linea(0), linea(1, 3), linea(3, 3)], practica=True, respuesta='SILENCIO')
        self.assertEqual(r.respuestas_descartadas, 1)

    def test_demora_invalida(self):
        with self.assertRaises(ValueError):
            reproducir([], demora=-1)
