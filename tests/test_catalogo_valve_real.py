"""Regresion sobre la captura publica de Valve del 26/11/2026."""
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path
from coach.datos.catalogo_heroes import CatalogoHeroes, importar_heroes

RECURSOS = Path(__file__).resolve().parents[1] / 'coach' / 'datos' / 'recursos'


class TestCatalogoValveReal(unittest.TestCase):
    def setUp(self):
        self.bruto = (RECURSOS / 'heroes_valve.json').read_bytes()
        self.catalogo = CatalogoHeroes(importar_heroes(json.loads(self.bruto.decode('utf-8-sig'))))
        self.snapshot = json.loads((RECURSOS / 'heroes_catalogo.json').read_text(encoding='utf-8'))

    def test_cobertura_captura(self):
        self.assertEqual(len(self.catalogo.heroes), 127)
        self.assertEqual(Counter(h.atributo for h in self.catalogo.heroes), {0: 36, 1: 34, 2: 34, 3: 23})
        self.assertEqual(Counter(h.complejidad for h in self.catalogo.heroes), {1: 55, 2: 59, 3: 13})

    def test_identidades_conocidas(self):
        for ident, clave, nombre in ((14, 'pudge', 'Pudge'), (44, 'phantom_assassin', 'Phantom Assassin'), (39, 'queenofpain', 'Queen of Pain'), (155, 'largo', 'Largo')):
            h = self.catalogo.por_id(ident)
            self.assertEqual(h.nombre, nombre)
            self.assertEqual(h, self.catalogo.por_clave('npc_dota_hero_' + clave))

    def test_integridad_snapshot(self):
        self.assertEqual(self.snapshot['sha256_origen'], hashlib.sha256(self.bruto).hexdigest())
        self.assertEqual(self.snapshot['heroes'], [vars(h) for h in self.catalogo.heroes])
        self.assertFalse(self.snapshot['parche_verificado'])
        self.assertEqual(self.snapshot['esquema'], 1)
