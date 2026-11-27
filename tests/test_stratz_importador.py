import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from actualizador_stratz import importar, catalogo, base_local

class TestImportador(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.db = self.root/'db.sqlite'; self.cat = self.root/'cat.json'; self.src = self.root/'data.json'
        self.cat.write_text(json.dumps({'heroes':[{'id':39},{'id':13}]}))
        f = dict(heroId1=39, heroId2=13, week=2968, bracketBasicIds='UNCALIBRATED', matchCount=100, winCount=50, synergy=1, winRateHeroId1=.5, winRateHeroId2=.5, winsAverage=.5)
        self.payload = {'data':{'heroStats':{'alternativa':[{'heroId':39,'with':[f.copy()],'vs':[f.copy()]}]}}}
    def ejecutar(self, rango='CRUSADER_ARCHON', alias='alternativa'):
        self.src.write_text(json.dumps(self.payload), encoding='utf-8-sig')
        return importar(self.src, alias, 39, rango, self.db, self.cat)
    def test_importar(self):
        self.assertEqual(self.ejecutar(), (2968,2,['UNCALIBRATED']))
    def test_repetir(self):
        self.ejecutar(); self.ejecutar()
        with closing(sqlite3.connect(self.db)) as c: self.assertEqual(c.execute('select count(*) from relaciones_v1').fetchone()[0],2)
    def test_incompleto(self):
        self.payload['data']['heroStats']['alternativa'][0]['vs']=[]
        with self.assertRaises(ValueError): self.ejecutar()
        self.assertFalse(self.db.exists())
    def test_error_graphql(self):
        self.payload['errors']=[{'message':'error'}]
        with self.assertRaises(ValueError): self.ejecutar()
        self.assertFalse(self.db.exists())
    def test_alias(self):
        with self.assertRaises(ValueError): self.ejecutar(alias='incorrecto')
    def test_rango(self):
        with self.assertRaises(ValueError): self.ejecutar(rango='')
    def test_rutas(self):
        self.assertEqual(catalogo().name,'heroes_catalogo.json'); self.assertIn('experimental',base_local().parts)
