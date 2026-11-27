import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from coach.draft.roles import ReconocedorRoles
from coach.draft.estado import CASILLAS

class TestRolesDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reconocedor = ReconocedorRoles()
        cls.carpeta = Path(__file__).resolve().parents[1] / 'coach' / 'draft' / 'recursos_roles'

    def imagen(self, rol):
        with Image.open(self.carpeta / f'rol_{rol}.png') as im:
            return im.copy()

    def test_cinco_roles(self):
        for rol in range(1,6):
            with self.subTest(rol=rol):
                self.assertEqual(self.reconocedor.reconocer(self.imagen(rol)).rol, rol)

    def test_escala(self):
        im = self.imagen(2)
        self.assertEqual(self.reconocedor.reconocer(im.resize((im.width*2,im.height*2))).rol,2)

    def test_vacio(self):
        self.assertIsNone(self.reconocedor.reconocer(Image.new('RGB',(80,14),'#34434a')).rol)

    def test_uniforme_claro(self):
        self.assertIsNone(self.reconocedor.reconocer(Image.new('RGB',(80,14),'white')).rol)

    def test_entrada_invalida(self):
        with self.assertRaises(ValueError): self.reconocedor.reconocer(None)

    def test_biblioteca_incompleta(self):
        with TemporaryDirectory() as carpeta:
            with self.assertRaises(FileNotFoundError): ReconocedorRoles(carpeta)

    def test_sin_roles_visibles(self):
        resultados = self.reconocedor.analizar(Image.new('RGB',(2048,857),'#34434a'))
        self.assertEqual(set(resultados),set(CASILLAS))
        self.assertTrue(all(v.rol is None for v in resultados.values()))

    def test_rol_independiente_del_lado(self):
        from coach.draft.diagnostico_ranked import recortes_ranked
        from coach.draft.captura import regiones
        im = Image.new('RGB',(2048,857),'#34434a')
        r = regiones(*im.size)['derecha_3']
        s = im.height / 800
        y0,y1 = round(80*s),round(93*s)
        im.paste(self.imagen(4).resize((r.ancho,y1-y0)),(r.x,y0))
        self.assertEqual(self.reconocedor.analizar(im)['derecha_3'].rol,4)
