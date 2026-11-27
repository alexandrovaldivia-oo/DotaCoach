import tempfile
import unittest
from pathlib import Path
from coach.draft.stratz_almacen import AlmacenStratz
from coach.draft.stratz_lector import auditar, consultar, intervalo_wilson

class TestLector(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.p=Path(t.name)/'datos.sqlite'
        a=AlmacenStratz(self.p)
        a.guardar(2968,'CRUSADER_ARCHON',39,[(r,13,'UNCALIBRATED',100,45,-2,.48,.49) for r in ('with','vs')]); a.cerrar()
    def consulta(self, otro=13, semana=None):
        return consultar(self.p,2968,'CRUSADER_ARCHON',39,'vs',otro,semana)
    def test_auditoria(self):
        d=auditar(self.p,{39,13}); self.assertEqual(d['total'],2); self.assertEqual(d['lotes'][0]['aliados'],1)
    def test_consulta(self):
        d=self.consulta(); self.assertEqual(d['tasa'],.45); self.assertFalse(d['rango_certificado']); self.assertIsNone(d['desactualizado'])
    def test_ausente(self): self.assertIsNone(self.consulta(86))
    def test_vigencia(self): self.assertTrue(self.consulta(semana=2969)['desactualizado']); self.assertFalse(self.consulta(semana=2968)['desactualizado'])
    def test_solo_lectura(self):
        antes=self.p.read_bytes(); auditar(self.p,{39,13}); self.consulta(); self.assertEqual(antes,self.p.read_bytes())
    def test_no_crea(self):
        p=self.p.with_name('ausente.sqlite')
        with self.assertRaises(Exception): auditar(p,{39,13})
        self.assertFalse(p.exists())
    def test_catalogo_incompleto(self):
        with self.assertRaises(ValueError): auditar(self.p,{39,13,86})
    def test_wilson(self):
        a,b=intervalo_wilson(50,100); self.assertAlmostEqual(a,.40383,places=4); self.assertAlmostEqual(b,.59617,places=4)
        with self.assertRaises(ValueError): intervalo_wilson(2,1)
