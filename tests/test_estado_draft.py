import unittest
from coach.datos.catalogo_heroes import CatalogoHeroes, Heroe
from coach.draft.estado import CASILLAS, interpretar
from coach.draft.reconocimiento import Coincidencia

class TestEstadoDraft(unittest.TestCase):
    def setUp(self):
        self.cat = CatalogoHeroes(Heroe(i, 'npc_dota_hero_h'+str(i), 'H'+str(i), 0, 1) for i in range(1, 12))
        self.c = {k:Coincidencia('h'+str(i), .95, .3) for i,k in enumerate(CASILLAS,1)}
        self.vacias = ('izquierda_5','derecha_5')
        for k in self.vacias: self.c[k] = Coincidencia(None,0,0)
        self.kw = dict(catalogo=self.cat, lado_propio='derecha',casilla_propia='derecha_5',confirmadas=set(CASILLAS)-set(self.vacias),vacias=self.vacias,vetados=('h11',),rol=2,turno_propio_confirmado=True)
    def evaluar(self, **kw):
        return interpretar(self.c, **(self.kw | kw))
    def test_derecha(self):
        e=self.evaluar(); self.assertTrue(e.listo_ultimo_pick); self.assertEqual(e.aliados,('h6','h7','h8','h9'))
    def test_izquierda(self):
        e=self.evaluar(lado_propio='izquierda',casilla_propia='izquierda_5'); self.assertTrue(e.listo_ultimo_pick); self.assertEqual(e.aliados,('h1','h2','h3','h4'))
    def test_lado_desconocido(self):
        e=self.evaluar(lado_propio=None,casilla_propia=None); self.assertFalse(e.listo_ultimo_pick); self.assertEqual(e.aliados,())
    def test_vetos_desconocidos(self): self.assertFalse(self.evaluar(vetados=None).listo_ultimo_pick)
    def test_rol_desconocido(self): self.assertFalse(self.evaluar(rol=None).listo_ultimo_pick)
    def test_turno_desconocido(self): self.assertFalse(self.evaluar(turno_propio_confirmado=False).listo_ultimo_pick)
    def test_preseleccion(self): self.assertFalse(self.evaluar(confirmadas=set(CASILLAS)-set(self.vacias)-{'derecha_1'}).listo_ultimo_pick)
    def test_identidad_desconocida(self):
        self.c['derecha_1']=Coincidencia(None,.7,.1); self.assertFalse(self.evaluar().listo_ultimo_pick)
    def test_duplicado(self):
        self.c['derecha_1']=self.c['izquierda_1']; self.assertIn('heroes_duplicados',self.evaluar().incidencias)
    def test_veto_conflicto(self): self.assertIn('seleccion_vetada',self.evaluar(vetados=('h1',)).incidencias)
    def test_vacia_con_retrato(self):
        self.c['derecha_5']=Coincidencia('h10',.95,.3); self.assertFalse(self.evaluar().listo_ultimo_pick)
    def test_anotaciones_invalidas(self):
        with self.assertRaises(ValueError): self.evaluar(rol=True)
        with self.assertRaises(ValueError): self.evaluar(vacias=('derecha_1',))
        with self.assertRaises(ValueError): self.evaluar(vetados=('inventado',))
