import unittest
from PIL import Image
from coach.draft.diagnostico_ranked import recortes_ranked
from coach.draft.estado import CASILLAS


class TestDiagnosticoRanked(unittest.TestCase):
    def test_diez_casillas(self):
        r = recortes_ranked(Image.new('RGB',(2048,857)))
        self.assertEqual(set(r),set(CASILLAS))
        self.assertTrue(all(set(v)=={'original','superior','rol'} for v in r.values()))

    def test_banda_superior_excluye_franja_inferior(self):
        im=Image.new('RGB',(1914,800),'black')
        im.paste('red',(0,32,1914,47))
        r=recortes_ranked(im)['izquierda_1']
        self.assertEqual(r['superior'].getbbox(),None)
        self.assertIsNotNone(r['original'].getbbox())

    def test_resoluciones(self):
        for size in ((2048,857),(2047,930),(2048,860),(1920,1080)):
            with self.subTest(size=size):
                r=recortes_ranked(Image.new('RGB',size))
                self.assertTrue(all(v['superior'].height < v['original'].height for v in r.values()))

    def test_entrada_invalida(self):
        with self.assertRaises(TypeError): recortes_ranked(None)

    def test_escala_invalida(self):
        with self.assertRaises(ValueError): recortes_ranked(Image.new('RGB',(2048,857)),0)
