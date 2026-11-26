import unittest
from dataclasses import replace
from coach.state import parsear, EstadoPartida, Habilidad, Objeto
from coach.eventos_avanzados import detectar_avanzados


def estado():
    return parsear({'map': {'matchid':'1','paused':False,'clock_time':100,'game_state':'DOTA_GAMERULES_STATE_GAME_IN_PROGRESS'}, 'hero':{'name':'npc_dota_hero_pudge','level':6,'alive':True,'health_percent':80,'mana_percent':80}, 'player':{'kills':0,'deaths':0,'kill_streak':0}, 'items':{k:{'name':'empty'} for k in ['slot%d'%i for i in range(9)]+['stash%d'%i for i in range(6)]}})

class PruebasAvanzadas(unittest.TestCase):
    def setUp(self): self.a=estado()
    def tipos(self,b,a=None): return [e.tipo for e in detectar_avanzados(self.a if a is None else a,b)]
    def test_umbrales(self):
        b=replace(self.a,vida_porcentaje=25,mana_porcentaje=20)
        self.assertEqual(self.tipos(b),['vida_baja','mana_baja'])
        self.assertEqual(self.tipos(b,b),[])
        self.assertEqual(self.tipos(self.a,b),['vida_recuperada','mana_recuperada'])
    def test_desconocidos(self):
        self.assertEqual(self.tipos(replace(self.a,vida_porcentaje=None,mana_porcentaje=None)),[])
        self.assertEqual(self.tipos(self.a,EstadoPartida()),[])
    def test_muerte_unica(self):
        b=replace(self.a,vivo=False,deaths=1,vida_porcentaje=0)
        self.assertEqual(self.tipos(b),['muerte'])
        self.assertEqual(self.tipos(replace(b,vivo=True),b),['reaparicion'])
    def test_carga_sin_muerte(self):
        self.assertEqual(self.tipos(replace(self.a,vivo=False,conocidos=frozenset())),[])
    def test_fase(self):
        self.assertEqual(self.tipos(replace(self.a,fase='DOTA_GAMERULES_STATE_HERO_SELECTION',deaths=2)),['fase'])
    def test_pausa(self):
        b=replace(self.a,pausa=True,deaths=1)
        self.assertEqual(self.tipos(b),['pausa'])
        self.assertEqual(self.tipos(replace(b,pausa=False),b),['reanudacion'])
    def test_partida_distinta(self):
        self.assertEqual(self.tipos(replace(self.a,match_id='2',nivel=10)),['partida_nueva'])
    def test_reloj_retrocede(self):
        self.assertEqual(self.tipos(replace(self.a,reloj=1,kills=10)),[])
    def test_nivel_y_racha(self):
        b=replace(self.a,nivel=9,kills=5,racha=5)
        self.assertEqual(self.tipos(b),['nivel','kill','racha'])
        self.assertEqual(self.tipos(replace(b,racha=6),b),[])
    def test_definitiva(self):
        h=Habilidad('ability3','pudge_dismember',nivel=1,definitiva=True,pasiva=False,recarga=4,disponible=False)
        a=replace(self.a,detalle_habilidades=(h,))
        b=replace(a,detalle_habilidades=(replace(h,recarga=0,disponible=True),))
        self.assertEqual(self.tipos(b,a),['definitiva_disponible'])
        self.assertEqual(self.tipos(b,b),[])
    def test_inventario(self):
        def inv(**kw): return tuple(replace(o,nombre=kw.get(o.casilla,o.nombre)) for o in self.a.inventario)
        a=replace(self.a,inventario=inv(slot0='item_branches'))
        b=replace(a,inventario=inv(slot1='item_branches'))
        self.assertEqual(self.tipos(b,a),['item_movido'])
        c=replace(b,inventario=inv(slot0='item_branches',slot1='item_branches'))
        self.assertEqual(self.tipos(c,b),['item_incorporado'])
        self.assertEqual(self.tipos(b,c),['item_retirado'])
        self.assertEqual(self.tipos(replace(b,inventario=()),b),[])
