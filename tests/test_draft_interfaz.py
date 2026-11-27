import unittest
from unittest.mock import patch
from draft_offline import catalogo_local, analizar_formulario, resumen

class TestInterfazDraft(unittest.TestCase):
    def setUp(self):
        self.cat=catalogo_local()
        self.campos=dict(semana='2968',rango='CRUSADER_ARCHON',rol='2',aliados='8,100,2,3',enemigos='13,4,5,6',vetados='7',disponibles='39,86',repertorio='39,86',modo='personal',archivado=True,fase=True,turno=True)
    def test_conversion(self):
        with patch('draft_offline.analizar_sesion') as motor:
            analizar_formulario(self.campos,catalogo=self.cat,ruta='test')
            kw=motor.call_args.kwargs
            self.assertEqual(kw['disponibles'],[39,86]); self.assertEqual(kw['rol'],2)
            self.assertTrue(all(e.dominio is None for e in kw['repertorio'].entradas))
    def test_invalidos(self):
        with self.assertRaises(ValueError): analizar_formulario(dict(self.campos,aliados='abc'),catalogo=self.cat,ruta='test')
    def test_resumen(self):
        self.assertIn('No existe comparacion',resumen(dict(candidatos=[],comparacion_descriptiva_disponible=False)))
    def test_confirmacion(self):
        with self.assertRaises(ValueError): analizar_formulario(dict(self.campos,archivado=False),catalogo=self.cat,ruta='test')
