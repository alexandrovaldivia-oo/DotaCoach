import unittest
from pathlib import Path
from unittest.mock import patch
from draft_offline import catalogo_local
from coach.draft.contexto_conversacional import Contexto, actualizar, analizar, validar, resolver
from coach.draft.repertorio import Repertorio

class TestContexto(unittest.TestCase):
    def setUp(self): self.cat=catalogo_local(); self.c=Contexto(archivado=True)
    def a(self,s,c=None): return actualizar(c or self.c,s,self.cat)
    def test_nombres(self): self.assertEqual(resolver(self.cat,'QoP'),39)
    def test_rol(self): self.assertEqual(self.a('Soy mid').rol,2); self.assertEqual(self.a('Juego de 5').rol,5)
    def test_contexto(self):
        c=self.a('Aliados: Lion, Axe'); c=self.a('Mi Axe juega de 5',c); self.assertEqual(c.roles_declarados,((2,5),)); self.assertEqual(c.rol,2)
    def test_nueve(self):
        c=self.a('Aliados: Lion, Axe, Tusk, Juggernaut'); c=self.a('Enemigos: Puck, Bane, Crystal Maiden, Drow Ranger, Sven',c); self.assertEqual(len(c.aliados+c.enemigos),9)
    def test_duplicado(self):
        with self.assertRaises(ValueError): self.a('Aliados: Axe, Axe')
    def test_solapado(self):
        with self.assertRaises(ValueError): self.a('Candidatos: Axe',self.a('Aliados: Axe'))
    def test_desconocido(self):
        with self.assertRaises(ValueError): self.a('Aliados: desconocido')
    def test_no_archivado(self):
        with self.assertRaises(ValueError): validar(Contexto(),self.cat)
    def test_rol_no_aliado(self):
        with self.assertRaises(ValueError): self.a('Mi Axe juega de 5')
    def test_primer_pick(self):
        c=self.a('Candidatos: Queen of Pain'); r=analizar(c,catalogo=self.cat,repertorio=Repertorio(()),ruta=None,semana=2968,rango='X'); self.assertIsNone(r['filas'][0]['media']); self.assertFalse(r['recomendacion_disponible'])
    def test_parcial(self):
        c=self.a('Candidatos: Queen of Pain',self.a('Aliados: Axe'))
        with patch('coach.draft.contexto_conversacional.estadistica',return_value={'partidas':200,'tasa':.5}):
            r=analizar(c,catalogo=self.cat,repertorio=Repertorio(()),ruta=None,semana=2968,rango='X')
        self.assertEqual(r['filas'][0]['media'],.5); self.assertFalse(r['meta_verificado'])
