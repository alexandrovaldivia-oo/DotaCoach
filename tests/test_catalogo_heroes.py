import unittest
import tempfile
import json
from pathlib import Path
from coach.datos.catalogo_heroes import importar_heroes, CatalogoHeroes, guardar_catalogo


def fila(**cambios):
    base = dict(id=1, name='npc_dota_hero_antimage', name_loc='Anti-Mage', primary_attr=1, complexity=1)
    base.update(cambios)
    return base


def feed(*filas):
    return {'result': {'data': {'heroes': list(filas)}}}


class TestCatalogoHeroes(unittest.TestCase):
    def test_identidad(self):
        c = CatalogoHeroes(importar_heroes(feed(fila())))
        self.assertEqual(c.por_id(1).nombre, 'Anti-Mage')
        self.assertEqual(c.por_clave('npc_dota_hero_antimage'), c.por_id(1))
        self.assertIsNone(c.por_id(True))
        self.assertIsNone(c.por_id(999))

    def test_desconocidos(self):
        h, = importar_heroes(feed(fila(primary_attr=True, complexity=99)))
        self.assertIsNone(h.atributo)
        self.assertIsNone(h.complejidad)
        h, = importar_heroes(feed(fila(primary_attr=0)))
        self.assertEqual(h.atributo, 0)

    def test_duplicados(self):
        for segunda in (fila(name='npc_dota_hero_test'), fila(id=2)):
            with self.assertRaises(ValueError):
                importar_heroes(feed(fila(), segunda))

    def test_invalidos(self):
        for datos in ({}, feed(), feed(fila(id=True)), feed(fila(name_loc=' ')), feed(fila(name='../test'))):
            with self.assertRaises(ValueError):
                importar_heroes(datos)

    def test_orden(self):
        h = importar_heroes(feed(fila(id=2, name='npc_dota_hero_test'), fila()))
        self.assertEqual([x.id for x in h], [1, 2])

    def test_guardado(self):
        with tempfile.TemporaryDirectory() as d:
            origen, destino = Path(d)/'raw.json', Path(d)/'catalogo.json'
            origen.write_text(json.dumps(feed(fila())), encoding='utf-8-sig')
            guardar_catalogo(origen, destino, '7.42a')
            datos = json.loads(destino.read_text(encoding='utf-8'))
            self.assertFalse(datos['parche_verificado'])
            self.assertEqual(len(datos['sha256_origen']), 64)
            self.assertEqual(datos['heroes'][0]['nombre'], 'Anti-Mage')
            previo = destino.read_bytes()
            origen.write_text('{}')
            with self.assertRaises(ValueError):
                guardar_catalogo(origen, destino, '7.42a')
            self.assertEqual(destino.read_bytes(), previo)

    def test_parche_invalido(self):
        with self.assertRaises(ValueError):
            guardar_catalogo('no-existe', 'no-existe', '../7.42a')
