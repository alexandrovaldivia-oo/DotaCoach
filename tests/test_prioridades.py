import unittest
from dataclasses import replace
from coach.eventos import Evento
from coach.prioridades import ControlAvisos
from coach.state import parsear


def estado():
    return parsear({'map':{'matchid':'1','paused':False,'game_state':'DOTA_GAMERULES_STATE_GAME_IN_PROGRESS'},'hero':{'name':'npc_dota_hero_pudge','level':6,'alive':True,'health_percent':20,'mana_percent':10}})


class TestPrioridades(unittest.TestCase):
    def setUp(self):
        self.c = ControlAvisos()
        self.e = estado()

    def elegir(self, tipos, t=0, estado=None, **kw):
        opciones = dict(practica=True, ia_disponible=True, ia_ocupada=False)
        opciones.update(kw)
        return self.c.seleccionar([Evento(x) for x in tipos], estado or self.e, t, **opciones)

    def test_bloqueo_por_defecto(self):
        self.assertIsNone(self.c.seleccionar([Evento('vida_baja')], self.e, 0))
        self.assertIsNone(self.elegir(['vida_baja'], practica=False))

    def test_prioridad_y_un_solo_aviso(self):
        self.assertEqual(self.elegir(['mana_baja','vida_baja','racha']).tipo, 'vida_baja')
        self.assertIsNone(self.elegir([], 20))

    def test_intervalo_global(self):
        self.elegir(['vida_baja'])
        self.assertIsNone(self.elegir(['definitiva_disponible'], 5))
        self.assertEqual(self.elegir(['definitiva_disponible'], 6).tipo, 'definitiva_disponible')

    def test_histeresis_vida(self):
        self.elegir(['vida_baja'])
        self.elegir([], 25, replace(self.e, vida_porcentaje=30))
        self.assertIsNone(self.elegir(['vida_baja'], 26))
        self.elegir([], 27, replace(self.e, vida_porcentaje=35))
        self.assertEqual(self.elegir(['vida_baja'], 28).tipo, 'vida_baja')

    def test_histeresis_mana(self):
        self.elegir(['mana_baja'])
        self.elegir([], 31, replace(self.e, mana_porcentaje=25))
        self.assertIsNone(self.elegir(['mana_baja'], 32))
        self.elegir([], 33, replace(self.e, mana_porcentaje=30))
        self.assertEqual(self.elegir(['mana_baja'], 34).tipo, 'mana_baja')

    def test_pausa_y_fase(self):
        for e in (replace(self.e, pausa=True), replace(self.e, pausa=None), replace(self.e, fase='seleccion')):
            self.assertIsNone(self.elegir(['vida_baja'], estado=e))

    def test_desconocido(self):
        self.assertIsNone(self.elegir(['vida_baja'], estado=replace(self.e, vida_porcentaje=None)))
        self.assertIsNone(self.elegir(['mana_baja'], estado=replace(self.e, conocidos=frozenset())))

    def test_muerte_doble(self):
        muerto = replace(self.e, vivo=False)
        self.assertEqual(self.elegir(['muerte'], estado=muerto).tipo, 'muerte')
        self.assertIsNone(self.elegir(['muerte'], 10, muerto))
        self.assertIsNone(self.elegir(['vida_baja'], 20, muerto))

    def test_ia_ocupada_o_no_disponible(self):
        self.assertIsNone(self.elegir(['racha'], ia_ocupada=True))
        self.assertIsNone(self.elegir(['racha'], ia_disponible=False))
        self.assertEqual(self.elegir(['racha','vida_baja'], ia_ocupada=True).tipo, 'vida_baja')

    def test_intervalo_ia(self):
        self.assertTrue(self.elegir(['racha']).usa_ia)
        self.assertIsNone(self.elegir(['item_incorporado'], 24))
        self.assertTrue(self.elegir(['item_incorporado'], 25).usa_ia)

    def test_informativos(self):
        self.assertIsNone(self.elegir(['item_movido','item_retirado','nivel','fase','kill','reaparicion']))

    def test_nueva_sesion(self):
        self.elegir(['vida_baja'])
        self.assertEqual(self.elegir(['vida_baja'], 7, replace(self.e, match_id='2')).tipo,'vida_baja')

    def test_reloj(self):
        self.elegir([], 10)
        with self.assertRaises(ValueError): self.elegir([], 9)
        with self.assertRaises(ValueError): self.elegir([], float('nan'))
