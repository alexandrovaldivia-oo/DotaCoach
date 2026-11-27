import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageEnhance
from coach.draft.reconocimiento_ranked import ReconocedorRanked, bandas_ranked
from coach.draft.estado import CASILLAS
from test_reconocimiento_draft import biblioteca, dibujo


class TestReconocimientoRanked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.ruta = Path(cls.tmp.name)/'refs.zip'
        biblioteca(cls.ruta)
        cls.r = ReconocedorRanked(cls.ruta)

    def test_bandas(self):
        for size in ((2048,857),(2047,930),(2048,860),(1920,1080)):
            with self.subTest(size=size):
                im = Image.new('RGB',size)
                im.paste('red',(0,round(size[1]*.04),size[0],size[1]))
                bandas = bandas_ranked(im)
                self.assertEqual(set(bandas),set(CASILLAS))
                self.assertTrue(all(b.getbbox() is None for b in bandas.values()))

    def test_reconoce_parcial(self):
        for i,n in enumerate(('alfa','beta')):
            im = dibujo(i)
            banda = im.crop((int(.15*im.width),int(.08*im.height),int(.85*im.width),int(.55*im.height)))
            self.assertEqual(self.r.reconocer(banda).heroe,n)

    def test_gris(self):
        banda = ImageEnhance.Color(dibujo(0)).enhance(0).convert('RGB')
        self.assertIsNone(self.r.reconocer(banda).heroe)

    def test_atenuada(self):
        im = dibujo(0)
        banda = im.crop((14,4,81,29))
        banda = ImageEnhance.Color(banda).enhance(.4)
        self.assertIsNone(self.r.reconocer(banda).heroe)

    def test_vacia(self):
        self.assertTrue(all(c.heroe is None for c in self.r.reconocer_captura(Image.new('RGB',(2048,857))).values()))

    def test_ambigua(self):
        ruta = Path(self.tmp.name)/'ambigua.zip'
        biblioteca(ruta,identicos=True)
        im = dibujo(0)
        self.assertIsNone(ReconocedorRanked(ruta).reconocer(im.crop((14,4,81,29))).heroe)

    def test_biblioteca_incompleta(self):
        ruta = Path(self.tmp.name)/'incompleta.zip'
        biblioteca(ruta,incompleta=True)
        with self.assertRaises(KeyError): ReconocedorRanked(ruta)

    def test_parametros_invalidos(self):
        for kwargs in ({'umbral':0},{'margen':0},{'proporcion_color':0},{'cromaticidad_minima':256}):
            with self.assertRaises(ValueError): ReconocedorRanked(self.ruta,**kwargs)
        with self.assertRaises(ValueError): self.r.reconocer(Image.new('RGB',(4,4)))
        with self.assertRaises(ValueError): bandas_ranked(Image.new('RGB',(2048,857)),0)
