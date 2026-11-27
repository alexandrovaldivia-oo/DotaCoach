import unittest
import random
from PIL import Image, ImageDraw
from coach.datos.catalogo_heroes import CatalogoHeroes, Heroe
from coach.draft.cuadricula import ReconocedorCuadricula, recortar_cuadricula, vetos_probables, CasillaIdentificada

class TestCuadricula(unittest.TestCase):
    def setUp(self):
        self.catalogo=CatalogoHeroes([Heroe(i,'npc_dota_hero_'+str(i),str(i),0,1) for i in (1,2,3)])
        self.refs={}
        for i in (1,2,3):
            rng=random.Random(i)
            im=Image.new('RGB',(40,60))
            d=ImageDraw.Draw(im)
            for x in range(0,40,5):
                for y in range(0,60,5):
                    p=rng.randrange(25,210);d.rectangle((x,y,x+4,y+4),fill=(p,p,p))
            self.refs[i]=im
        self.rec=ReconocedorCuadricula(self.refs,self.catalogo)
    def test_identidad(self):
        self.assertEqual(self.rec.reconocer(self.refs[2]).heroe_id,2)
    def test_orden_independiente(self):
        r=self.rec.analizar({'z':self.refs[3],'a':self.refs[1]})
        self.assertEqual((r['z'].heroe_id,r['a'].heroe_id),(3,1))
    def test_uniforme(self):
        self.assertIsNone(self.rec.reconocer(Image.new('RGB',(40,60))).heroe_id)
    def test_duplicados(self):
        r=self.rec.analizar({'a':self.refs[1],'b':self.refs[1]})
        self.assertTrue(all(v.heroe_id is None for v in r.values()))
    def test_ambiguo(self):
        r=ReconocedorCuadricula({1:self.refs[1],2:self.refs[1],3:self.refs[3]},self.catalogo)
        self.assertIsNone(r.reconocer(self.refs[1]).heroe_id)
    def test_incompleto(self):
        with self.assertRaises(ValueError): ReconocedorCuadricula({1:self.refs[1]},self.catalogo)
    def test_caja(self):
        self.assertEqual(recortar_cuadricula(self.refs[1],{'x':(0,0,30,40)})['x'].size,(30,40))
        with self.assertRaises(ValueError): recortar_cuadricula(self.refs[1],{'x':(0,0,41,60)})
    def test_vetos_no_certificados(self):
        r={'a':CasillaIdentificada(1,.9,.3,'marca_probable'),'b':CasillaIdentificada(None,.9,.3,'marca_probable'),'c':CasillaIdentificada(2,.9,.3,'dudosa')}
        self.assertEqual(vetos_probables(r),frozenset({1}))
