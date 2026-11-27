import json
import unittest
from pathlib import Path
from dataclasses import replace
from coach.datos.catalogo_heroes import CatalogoHeroes, importar_heroes
from coach.draft.capacidades import PILOTO, validar_perfiles, consultar, Perfil

class TestCapacidades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ruta = Path(__file__).resolve().parents[1] / 'coach/datos/recursos/heroes_valve.json'
        cls.catalogo = CatalogoHeroes(importar_heroes(json.loads(ruta.read_text(encoding='utf-8-sig'))))
        cls.perfiles = validar_perfiles(PILOTO, cls.catalogo)
    def test_identidades(self):
        self.assertEqual(set(self.perfiles), {39,13,86})
        self.assertEqual(self.catalogo.por_id(39).nombre, 'Queen of Pain')
    def test_desconocido(self):
        self.assertEqual(consultar(self.perfiles,self.catalogo,39).estado('estructuras'),'desconocido')
    def test_sin_perfil(self):
        self.assertEqual(consultar(self.perfiles,self.catalogo,2).estado('movilidad'),'desconocido')
    def test_condicional(self):
        self.assertEqual(self.perfiles[13].estado('aturdimiento'),'condicional')
    def test_inferido(self):
        self.assertEqual(self.perfiles[39].estado('escape'),'inferido')
    def test_documentado(self):
        self.assertEqual(self.perfiles[39].estado('movilidad'),'documentado')
    def test_id_invalido(self):
        with self.assertRaises(ValueError): consultar(self.perfiles,self.catalogo,-1)
    def test_duplicado(self):
        with self.assertRaises(ValueError): validar_perfiles((PILOTO[0],PILOTO[0]),self.catalogo)
    def test_fuente(self):
        p=PILOTO[0]
        with self.assertRaises(ValueError): validar_perfiles((Perfil(39,(replace(p.evidencias[0],fuente=''),)),),self.catalogo)
    def test_parche_no_certificado(self):
        self.assertTrue(all(e.parche is None for p in PILOTO for e in p.evidencias))
    def test_capacidad_invalida(self):
        with self.assertRaises(ValueError): self.perfiles[39].estado('inventado')
    def test_evidencia_duplicada(self):
        e=PILOTO[0].evidencias[0]
        with self.assertRaises(ValueError): validar_perfiles((Perfil(39,(e,e)),),self.catalogo)
