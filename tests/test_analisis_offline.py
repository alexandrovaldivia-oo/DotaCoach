import json
import tempfile
import unittest
from pathlib import Path
from coach.datos.catalogo_heroes import CatalogoHeroes, importar_heroes
from coach.draft.analisis_offline import comparar, PERFILES
from coach.draft.capacidades import validar_perfiles
from coach.draft.repertorio import Repertorio, Preferencia
from coach.draft.ultimo_pick import UltimoPick
from coach.draft.stratz_almacen import AlmacenStratz

class TestAnalisisOffline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parents[1]/'coach/datos/recursos/heroes_valve.json'
        cls.cat=CatalogoHeroes(importar_heroes(json.loads(p.read_text(encoding='utf-8-sig'))))
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.ruta=Path(self.tmp.name)/'test.sqlite3'
        a=AlmacenStratz(self.ruta)
        a.guardar(2968,'CRUSADER_ARCHON',39,[('vs',13,'UNCALIBRATED',1018,458,-5.187,.478,.477)])
        a.cerrar()
        self.args=dict(catalogo=self.cat,repertorio=Repertorio((Preferencia(2,39,None),)),ultimo_pick=UltimoPick(True,frozenset({39,86,87}),()),aliados=(8,100,2,3),enemigos=(13,4,5,6),rol=2,ruta=self.ruta,semana=2968,rango='CRUSADER_ARCHON')
    def evaluar(self,**kw): return comparar(**(self.args|kw))
    def test_perfiles(self): self.assertEqual(len(validar_perfiles(PERFILES,self.cat)),6)
    def test_personal(self): self.assertEqual([x['heroe'] for x in self.evaluar(modo='personal')['candidatos']],[39])
    def test_estrategico(self): self.assertEqual(len(self.evaluar(modo='estrategico')['candidatos']),3)
    def test_equilibrado(self): self.assertEqual(len(self.evaluar()['candidatos']),3)
    def test_no_ranking(self): self.assertFalse(self.evaluar()['ranking_disponible'])
    def test_faltantes(self): self.assertEqual(next(x for x in self.evaluar()['candidatos'] if x['heroe']==39)['relaciones_presentes'],1)
    def test_dato_realista(self):
        x=next(x for x in self.evaluar()['candidatos'] if x['heroe']==39)
        d=next(d for r,j,d in x['relaciones'] if r=='vs' and j==13)
        self.assertEqual(d['victorias'],458); self.assertFalse(d['rango_certificado'])
    def test_desconocida(self): self.assertEqual(self.evaluar()['cobertura']['estructuras'],())
    def test_proteccion(self): self.assertEqual(self.evaluar()['cobertura']['proteccion'],((8,'inferido'),))
    def test_sin_confirmacion(self):
        with self.assertRaises(ValueError): self.evaluar(ultimo_pick=UltimoPick(False,frozenset(),('no',)))
    def test_seleccionada(self):
        with self.assertRaises(ValueError): self.evaluar(ultimo_pick=UltimoPick(True,frozenset({13}),()))
    def test_duplicados(self):
        with self.assertRaises(ValueError): self.evaluar(enemigos=(13,13,5,6))
    def test_posicion(self):
        with self.assertRaises(ValueError): self.evaluar(rol=0)
    def test_modo(self):
        with self.assertRaises(ValueError): self.evaluar(modo='otro')
    def test_no_escribe(self):
        antes=self.ruta.read_bytes(); self.evaluar(); self.assertEqual(antes,self.ruta.read_bytes())
