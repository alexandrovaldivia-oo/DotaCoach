import unittest
from coach.datos.catalogo_heroes import CatalogoHeroes, Heroe
from coach.draft.estadisticas import importar_opendota
from coach.draft.repertorio import cargar_repertorio


class TestEstadisticasDraft(unittest.TestCase):
    def setUp(self):
        self.cat = CatalogoHeroes([Heroe(i, f'npc_dota_hero_h{i}', f'H{i}', 0, 1) for i in range(1, 4)])
        self.fila = dict(hero_id=2, games_played=20, wins=12)

    def cargar(self, datos, **kw):
        args = dict(heroe_id=1, catalogo=self.cat, obtenido_utc='2026-11-27T00:00:00Z')
        args.update(kw)
        return importar_opendota(datos, **args)

    def test_tasa_y_procedencia(self):
        r = self.cargar([self.fila])
        self.assertEqual(r.filas[0].tasa, .6)
        self.assertIsNone(r.parche)
        self.assertEqual(r.poblacion, 'no_verificada_en_payload')
        self.assertTrue(r.fuente.endswith('/1/matchups'))

    def test_vacio(self):
        self.assertEqual(self.cargar([]).filas, ())

    def test_cero(self):
        self.assertIsNone(self.cargar([dict(self.fila, games_played=0, wins=0)]).filas[0].tasa)

    def test_duplicado(self):
        with self.assertRaises(ValueError): self.cargar([self.fila, self.fila])

    def test_invalidos(self):
        for k, v in [('hero_id', 1), ('hero_id', 99), ('games_played', -1), ('wins', 21), ('wins', True)]:
            with self.subTest(k=k, v=v), self.assertRaises(ValueError): self.cargar([dict(self.fila, **{k:v})])

    def test_formato(self):
        with self.assertRaises(ValueError): self.cargar({'error': 'test'})

    def test_fecha(self):
        with self.assertRaises(ValueError): self.cargar([], obtenido_utc='2026-11-27')

    def test_origen(self):
        with self.assertRaises(ValueError): self.cargar([], heroe_id=99)

    def test_dominio_desconocido(self):
        r = cargar_repertorio({'esquema':1, 'entradas':[{'rol':2,'heroe_id':1,'dominio':None}, {'rol':2,'heroe_id':2,'dominio':3}]}, catalogo=self.cat)
        self.assertEqual([e.dominio for e in r.entradas], [3, None])
