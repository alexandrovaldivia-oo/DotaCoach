import unittest, json, tempfile
from pathlib import Path
from coach.datos.catalogo_heroes import CatalogoHeroes, importar_heroes
from coach.draft.repertorio import Repertorio, Preferencia
from coach.draft.stratz_almacen import AlmacenStratz
from coach.draft.sesion_offline import analizar_sesion

class TestSesionOffline(unittest.TestCase):
    def setUp(self):
        p=Path(__file__).resolve().parents[1]/'coach/datos/recursos/heroes_valve.json'
        self.cat=CatalogoHeroes(importar_heroes(json.loads(p.read_text(encoding='utf-8-sig'))))
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.db=Path(t.name)/'test.sqlite3'
        a=AlmacenStratz(self.db)
        a.guardar(2968,'CRUSADER_ARCHON',39,[(r,h.id,'UNCALIBRATED',200,100,0.,.5,.5) for h in self.cat.heroes if h.id!=39 for r in ('with','vs')]); a.cerrar()
        self.args=dict(catalogo=self.cat,repertorio=Repertorio((Preferencia(2,39,None),)),ruta=self.db,semana=2968,rango='CRUSADER_ARCHON',rol=2,aliados=[8,100,2,3],enemigos=[13,4,5,6],vetados=[7],disponibles=[39,86],archivado=True,fase_confirmada=True,turno_confirmado=True)
    def run_case(self,**kw): return analizar_sesion(**(self.args|kw))
    def test_integracion(self):
        r=self.run_case(); self.assertEqual(len(r['candidatos']),2); self.assertFalse(r['recomendacion_disponible']); self.assertEqual({f['heroe']:f['relaciones_presentes'] for f in r['candidatos']},{39:8,86:0})
    def test_personal(self): self.assertEqual(len(self.run_case(modo='personal')['candidatos']),1)
    def test_no_escribe(self):
        b=self.db.read_bytes(); self.run_case(); self.assertEqual(b,self.db.read_bytes())
    def test_rechazos(self):
        for kw in (dict(archivado=False),dict(fase_confirmada=False),dict(turno_confirmado=False),dict(vetados=None),dict(disponibles=[7]),dict(disponibles=[13]),dict(disponibles=[39,39]),dict(aliados=[1]),dict(rol=True),dict(semana=1),dict(disponibles=[9999])):
            with self.subTest(kw=kw),self.assertRaises(ValueError): self.run_case(**kw)
