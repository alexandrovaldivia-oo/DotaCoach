import unittest
from unittest.mock import patch
from coach.draft.clasificacion_offline import clasificar


def fila(i, tasa=.5, n=200, faltan=0, personal=False):
    return dict(heroe=i,nombre=f'Heroe {i}',en_repertorio=personal,dominio=None,evidencias=(),relaciones=tuple(('with' if j<4 else 'vs',j,None if j<faltan else dict(partidas=n,tasa=tasa)) for j in range(8)))

class TestClasificacionOffline(unittest.TestCase):
    def evaluar(self,*filas,**kw):
        with patch('coach.draft.clasificacion_offline.comparar',return_value=dict(candidatos=filas, ranking_disponible=False)):
            return clasificar(**kw)
    def test_orden(self):
        self.assertEqual(self.evaluar(fila(1,.4),fila(2,.6))['orden_descriptivo'],(2,1))
    def test_faltantes(self):
        self.assertEqual(self.evaluar(fila(1),fila(2,faltan=1))['orden_descriptivo'],())
    def test_muestra(self):
        self.assertFalse(self.evaluar(fila(1),fila(2,n=99))['comparacion_descriptiva_disponible'])
    def test_unico(self):
        self.assertFalse(self.evaluar(fila(1))['comparacion_descriptiva_disponible'])
    def test_vacio(self):
        self.assertEqual(self.evaluar()['orden_descriptivo'],())
    def test_empate(self):
        self.assertEqual(self.evaluar(fila(2),fila(1))['orden_descriptivo'],(1,2))
    def test_no_recomendacion(self):
        r=self.evaluar(fila(1),fila(2)); self.assertFalse(r['ranking_disponible']); self.assertFalse(r['recomendacion_disponible'])
    def test_personal(self):
        self.assertIn('repertorio personal',self.evaluar(fila(1,personal=True))['candidatos'][0]['explicacion'])
    def test_minimo(self):
        with self.assertRaises(ValueError): self.evaluar(fila(1),minimo_partidas=0)
    def test_explicacion(self):
        self.assertIn('No es una probabilidad',self.evaluar(fila(1))['candidatos'][0]['explicacion'])
    def test_ausencia_no_cero(self):
        self.assertIsNone(self.evaluar(fila(1,faltan=8))['candidatos'][0]['media_descriptiva'])
