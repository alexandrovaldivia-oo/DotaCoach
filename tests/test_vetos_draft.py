import unittest
from PIL import Image, ImageDraw
from coach.draft.vetos import detectar_marca, analizar_casillas

class TestVetos(unittest.TestCase):
    def imagen(self, fondo=(28,43,48)):
        return Image.new('RGB',(40,60),fondo)

    def test_diagonal(self):
        im=self.imagen(); ImageDraw.Draw(im).line((5,55,35,5),fill=(114,63,68),width=4)
        self.assertEqual(detectar_marca(im).estado,'marca_probable')

    def test_uniforme(self):
        self.assertEqual(detectar_marca(self.imagen()).estado,'sin_marca_detectada')

    def test_rojo_uniforme(self):
        self.assertNotEqual(detectar_marca(self.imagen((120,40,40))).estado,'marca_probable')

    def test_rojo_horizontal(self):
        im=self.imagen(); ImageDraw.Draw(im).line((0,30,39,30),fill=(140,50,50),width=5)
        self.assertNotEqual(detectar_marca(im).estado,'marca_probable')

    def test_reescalado(self):
        im=self.imagen(); ImageDraw.Draw(im).line((5,55,35,5),fill=(114,63,68),width=5)
        self.assertEqual(detectar_marca(im.resize((80,120))).estado,'marca_probable')

    def test_region(self):
        im=self.imagen(); self.assertEqual(set(analizar_casillas(im,{'a':(0,0,40,60)})),{'a'})

    def test_region_fuera(self):
        with self.assertRaises(ValueError): analizar_casillas(self.imagen(),{'a':(-1,0,40,60)})

    def test_imagen_invalida(self):
        with self.assertRaises(ValueError): detectar_marca(Image.new('RGB',(5,5)))
