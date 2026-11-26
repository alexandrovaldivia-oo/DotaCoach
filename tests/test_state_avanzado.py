import unittest
from coach.state import parsear, EstadoPartida


class EstadoAvanzado(unittest.TestCase):
    def test_cero_ausente_invalido(self):
        e = parsear({'hero': {'mana': 0, 'health': 'x', 'alive': False}})
        self.assertEqual(e.mana, 0)
        self.assertIsNone(e.vida)
        self.assertIsNone(e.mana_maximo)
        self.assertIn('hero.mana', e.conocidos)
        self.assertIn('hero.health', e.invalidos)
        self.assertNotIn('hero.max_mana', e.invalidos)
        self.assertFalse(e.vivo)

    def test_booleanos_y_rangos(self):
        e = parsear({'hero': {'alive': 'false', 'health_percent': 101, 'mana': True, 'xpos': -20}, 'map': {'paused': False, 'clock_time': -85}})
        self.assertIsNone(e.vida_porcentaje)
        self.assertIsNone(e.mana)
        self.assertIn('hero.alive', e.invalidos)
        self.assertFalse(e.pausa)
        self.assertEqual((e.x, e.reloj), (-20, -85))

    def test_inventario_por_casilla(self):
        e = parsear({'items': {'slot0': {'name':'item_branches'}, 'slot1': {'name':'item_branches'}, 'slot2': {'name':'empty'}, 'slot3': {}, 'teleport0': {'name':'item_tpscroll', 'charges': 2, 'cooldown': 0}, 'neutral0': {'name':'empty'}}})
        d = {o.casilla:o for o in e.inventario}
        self.assertEqual(e.items, frozenset({'item_branches'}))
        self.assertEqual(d['slot0'].nombre, d['slot1'].nombre)
        self.assertTrue(d['slot2'].vacio)
        self.assertIsNone(d['slot3'].vacio)
        self.assertEqual(d['teleport0'].cargas, 2)
        self.assertEqual(d['teleport0'].recarga, 0)
        self.assertNotIn('slot4', d)

    def test_habilidades(self):
        e = parsear({'abilities': {'ability1': {'name':'phantom_assassin_phantom_strike', 'level': 3, 'can_cast': False, 'charges': 0, 'max_charges': 2, 'charge_cooldown': 4}}})
        a, = e.detalle_habilidades
        self.assertEqual((a.nivel, a.cargas, a.cargas_maximas, a.recarga_carga), (3, 0, 2, 4))
        self.assertFalse(a.disponible)
        self.assertIsNone(a.definitiva)
        self.assertEqual(e.habilidades, ((a.nombre, 3),))

    def test_fase_y_estadisticas(self):
        e = parsear({'map': {'game_state':'DOTA_GAMERULES_STATE_GAME_IN_PROGRESS', 'radiant_score':0, 'dire_score':2}, 'player': {'last_hits':0, 'denies':2,'gpm':400,'xpm':500,'gold':0}, 'hero': {'stunned':False}})
        self.assertTrue(e.fase_activa)
        self.assertEqual((e.ultimos_golpes,e.denegaciones,e.gpm,e.xpm,e.radiant,e.dire),(0,2,400,500,0,2))
        self.assertIn('player.gold',e.conocidos)
        self.assertFalse(dict(e.estados)['stunned'])
        self.assertIsNone(dict(e.estados)['silenced'])

    def test_no_arrastra_datos(self):
        parsear({'hero': {'health':900}, 'items':{'slot0':{'name':'item_blink'}}})
        e = parsear({'provider': {'name':'Dota 2'}, 'previously':{'hero':{'health':900}}})
        self.assertIsNone(e.vida)
        self.assertFalse(e.en_partida)
        self.assertEqual(e.inventario, ())
        self.assertEqual(parsear(None), EstadoPartida())

    def test_datos_malformados(self):
        e = parsear({'hero':{'name':None,'level':float('inf')}, 'items':{'slot0':{'name':[]}}, 'abilities':{'ability0':{'name':{},'level':True}}, 'map':[]})
        self.assertFalse(e.en_partida)
        self.assertEqual(e.items, frozenset())
        self.assertIsNone(e.detalle_habilidades[0].nivel)
        self.assertIn('items.slot0.name',e.invalidos)
