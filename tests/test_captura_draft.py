import unittest
from unittest.mock import patch
from PIL import Image
from coach.draft.captura import Region, regiones, recortar, capturar_practica


class TestCapturaDraft(unittest.TestCase):
    def test_regiones_ultraancha(self):
        r = regiones(2048, 857)
        self.assertEqual(len(r), 12)
        self.assertEqual(r['izquierda_1'].caja, (433, 5, 513, 50))
        self.assertLess(r['izquierda_5'].caja[2], r['temporizador'].x)
        self.assertLess(r['temporizador'].caja[2], r['derecha_1'].x)

    def test_geometrias(self):
        for w, h in [(1920,1080),(2560,1440),(3440,1440),(2048,856)]:
            for r in regiones(w,h).values():
                x,y,a,b = r.caja
                self.assertTrue(0 <= x < a <= w and 0 <= y < b <= h)

    def test_centrado(self):
        a = regiones(1920,1080)['temporizador']
        b = regiones(3440,1080)['temporizador']
        self.assertEqual(b.x-a.x, 760)
        self.assertEqual(a.ancho,b.ancho)

    def test_invalido(self):
        for w,h,s in [(0,800,1),(800,800,1),(2048,857,float('nan')),(2048,857,0),(2048,857,True)]:
            with self.assertRaises(ValueError):
                regiones(w,h,s)

    def test_recorte(self):
        im = Image.new('RGB',(2048,857))
        r = regiones(*im.size)['derecha_1']
        im.paste((255,0,0),r.caja)
        partes = recortar(im)
        self.assertEqual(partes['derecha_1'].size,(r.ancho,r.alto))
        self.assertEqual(partes['derecha_1'].getpixel((0,0)),(255,0,0))
        self.assertEqual(partes['izquierda_1'].getpixel((0,0)),(0,0,0))

    @patch('coach.draft.captura.ImageGrab.grab')
    def test_bloqueo(self, grab):
        with self.assertRaises(PermissionError):
            capturar_practica(Region(0,0,100,100))
        grab.assert_not_called()

    @patch('coach.draft.captura.ImageGrab.grab')
    def test_captura(self, grab):
        grab.return_value = Image.new('RGB',(100,80))
        self.assertEqual(capturar_practica(Region(-100,0,100,80),practica_confirmada=True).size,(100,80))
        grab.assert_called_once_with(bbox=(-100,0,0,80),all_screens=True)

    @patch('coach.draft.captura.ImageGrab.grab')
    def test_dimension_inesperada(self, grab):
        grab.return_value = Image.new('RGB',(50,80))
        with self.assertRaises(RuntimeError):
            capturar_practica(Region(0,0,100,80),practica_confirmada=True)
