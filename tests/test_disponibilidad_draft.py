import unittest
from coach.datos.catalogo_heroes import CatalogoHeroes, Heroe
from coach.draft.cuadricula import CasillaIdentificada
from coach.draft.disponibilidad import evaluar

class TestDisponibilidad(unittest.TestCase):
    def setUp(self):
        self.c = CatalogoHeroes(Heroe(i, 'npc_dota_hero_'+str(i),str(i),0,1) for i in range(1,5))
        self.r = {'a':CasillaIdentificada(1,.95,.2,'sin_marca_detectada'),
                  'b':CasillaIdentificada(2,.95,.2,'marca_probable'),
                  'c':CasillaIdentificada(3,.95,.2,'dudosa')}
    def evaluar(self, **kw):
        return evaluar(self.r,catalogo=self.c,**kw)
    def test_sin_anotaciones(self):
        self.assertEqual(self.evaluar().disponibles,frozenset())
    def test_confirmacion(self):
        self.assertEqual(self.evaluar(anotaciones={'a':'disponible'}).disponibles,{1})
    def test_veto(self):
        self.assertEqual(self.evaluar(anotaciones={'b':'disponible'}).excluidos,{2})
    def test_dudoso(self):
        self.assertEqual(self.evaluar(anotaciones={'c':'disponible'}).desconocidos,{1,3,4})
    def test_seleccionado(self):
        self.assertFalse(self.evaluar(anotaciones={'a':'disponible'},seleccionados=[1]).disponibles)
    def test_veto_manual(self):
        self.assertEqual(self.evaluar(anotaciones={'a':'vetado'}).excluidos,{1,2})
    def test_duplicados(self):
        self.r['d']=self.r['a']
        self.assertFalse(self.evaluar(anotaciones={'a':'disponible'}).disponibles)
    def test_identidad_incierta(self):
        self.r['a']=CasillaIdentificada(1,.70,.2,'sin_marca_detectada')
        self.assertFalse(self.evaluar(anotaciones={'a':'disponible'}).disponibles)
    def test_anotacion_invalida(self):
        with self.assertRaises(ValueError): self.evaluar(anotaciones={'z':'disponible'})
    def test_sin_arrastre(self):
        self.evaluar(anotaciones={'a':'disponible'})
        self.assertFalse(self.evaluar().disponibles)
