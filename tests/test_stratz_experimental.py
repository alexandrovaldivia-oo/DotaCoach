import copy
import json
import tempfile
import unittest
from pathlib import Path
from coach.draft.stratz_cliente import ClienteStratz, extraer
from coach.draft.stratz_validador import validar
from coach.draft.stratz_almacen import AlmacenStratz
from coach.draft.stratz_descargador import importar_archivo, descargar_lote, cargar_catalogo

RANGO = 'CRUSADER_ARCHON'
IDS = {39,13,86}

def grupo():
    return {'heroId':39, **{r:[dict(heroId1=39,heroId2=i,week=2968,bracketBasicIds='UNCALIBRATED',matchCount=100,winCount=47,synergy=-1.2,winRateHeroId1=.48,winRateHeroId2=.49,winsAverage=.47) for i in (13,86)] for r in ('with','vs')}}

def payload(g=None):
    return {'data':{'heroStats':{'matchUp':[grupo() if g is None else g]}}}

class TestStratz(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.ruta=Path(self.tmp.name)
        self.a=AlmacenStratz(self.ruta/'stats.sqlite'); self.addCleanup(self.a.cerrar)
    def test_red_bloqueada(self):
        with self.assertRaises(PermissionError): ClienteStratz('dummy')
    def test_transporte_simulado(self):
        c=ClienteStratz('dummy', autorizado=True, transporte=lambda b: (self.assertEqual(b['variables']['rangos'],[RANGO]) or payload()))
        self.assertEqual(c.consultar(39,RANGO),grupo())
    def test_error_graphql(self):
        p=payload();p['errors']=[{'message':'error'}]
        with self.assertRaises(ValueError): extraer(p)
    def test_grupo_vacio(self):
        with self.assertRaises(ValueError): extraer({'data':{'heroStats':{'matchUp':[]}}})
    def test_valido(self):
        w,f=validar(grupo(),39,RANGO,IDS);self.assertEqual((w,len(f)),(2968,4));self.assertEqual(f[0][2],'UNCALIBRATED')
    def test_campos_invalidos(self):
        for k,v in [('heroId1',86),('heroId2',999),('winCount',101),('matchCount',0),('synergy',float('nan')),('winsAverage',.6),('bracketBasicIds',None),('week',1)]:
            with self.subTest(k=k):
                g=grupo();g['with'][0][k]=v
                with self.assertRaises(ValueError): validar(g,39,RANGO,IDS)
    def test_duplicado(self):
        g=grupo();g['with'].append(g['with'][0])
        with self.assertRaises(ValueError): validar(g,39,RANGO,IDS)
    def test_cobertura(self):
        g=grupo();g['vs'].pop()
        with self.assertRaises(ValueError): validar(g,39,RANGO,IDS)
    def test_periodo(self):
        with self.assertRaises(ValueError): validar(grupo(),39,RANGO,IDS,2967)
    def test_guardar_y_reemplazar(self):
        w,f=validar(grupo(),39,RANGO,IDS)
        self.a.guardar(w,RANGO,39,f);self.a.guardar(w,RANGO,39,f)
        self.assertTrue(self.a.completo(w,RANGO,39,IDS));self.assertEqual(self.a.db.execute('SELECT count(*) FROM relaciones_v1').fetchone()[0],4)
    def test_rangos_separados(self):
        w,f=validar(grupo(),39,RANGO,IDS);self.a.guardar(w,RANGO,39,f);self.a.guardar(w,'ALL',39,f)
        self.assertEqual(self.a.db.execute('SELECT count(*) FROM relaciones_v1').fetchone()[0],8)
    def test_rollback(self):
        w,f=validar(grupo(),39,RANGO,IDS);self.a.guardar(w,RANGO,39,f)
        with self.assertRaises(Exception): self.a.guardar(w,RANGO,39,f+[f[0]])
        self.assertTrue(self.a.completo(w,RANGO,39,IDS))
    def test_importar(self):
        p=self.ruta/'muestra.json';p.write_text(json.dumps(payload()),encoding='utf-8-sig')
        self.assertEqual(importar_archivo(p,alias='matchUp',heroe=39,rango=RANGO,ids=IDS,almacen=self.a),(2968,4))
        g=grupo();g['vs'].pop();p.write_text(json.dumps(payload(g)))
        with self.assertRaises(ValueError): importar_archivo(p,alias='matchUp',heroe=39,rango=RANGO,ids=IDS,almacen=self.a)
        self.assertTrue(self.a.completo(2968,RANGO,39,IDS))
    def test_reanudar(self):
        c=ClienteStratz('dummy',autorizado=True,transporte=lambda b: payload())
        self.assertEqual(descargar_lote(c,self.a,heroe=39,rango=RANGO,ids=IDS),(2968,4))
        self.assertEqual(descargar_lote(None,self.a,heroe=39,rango=RANGO,ids=IDS,semana=2968),(2968,0))
    def test_catalogo(self):
        p=self.ruta/'catalogo.json';p.write_text(json.dumps({'heroes':[{'id':i} for i in IDS]}));self.assertEqual(cargar_catalogo(p),IDS)
