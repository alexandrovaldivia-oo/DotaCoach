import unittest
from coach.datos.catalogo_heroes import CatalogoHeroes, Heroe
from coach.draft.repertorio import cargar_repertorio, candidatos_personales
from coach.draft.ultimo_pick import UltimoPick


class TestRepertorio(unittest.TestCase):
    def setUp(self):
        self.cat = CatalogoHeroes([Heroe(i, f'npc_dota_hero_h{i}', f'H{i}', 0, 1) for i in range(1, 5)])
        self.filas = [{'rol': 2, 'heroe_id': 1, 'dominio': 1},
                      {'rol': 2, 'heroe_id': 2, 'dominio': 3},
                      {'rol': 1, 'heroe_id': 2, 'dominio': 2},
                      {'rol': 2, 'heroe_id': 3, 'dominio': 2}]

    def cargar(self, filas):
        return cargar_repertorio({'esquema': 1, 'entradas': filas}, catalogo=self.cat)

    def test_vacio(self):
        self.assertEqual(self.cargar([]).entradas, ())

    def test_orden_y_rol(self):
        r = self.cargar(self.filas)
        p = UltimoPick(True, frozenset({1, 2, 3}), ())
        self.assertEqual([e.heroe_id for e in candidatos_personales(r, p, rol=2)], [2, 3, 1])
        self.assertEqual([e.heroe_id for e in candidatos_personales(r, p, rol=1)], [2])

    def test_excluye_no_disponibles(self):
        p = UltimoPick(True, frozenset({1, 4}), ())
        self.assertEqual([e.heroe_id for e in candidatos_personales(self.cargar(self.filas), p, rol=2)], [1])

    def test_no_listo(self):
        self.assertEqual(candidatos_personales(self.cargar(self.filas), UltimoPick(False, frozenset({2}), ()), rol=2), ())

    def test_incidencias(self):
        self.assertEqual(candidatos_personales(self.cargar(self.filas), UltimoPick(True, frozenset({2}), ('conflicto',)), rol=2), ())

    def test_duplicado(self):
        with self.assertRaises(ValueError): self.cargar(self.filas + [self.filas[0]])

    def test_id_desconocido(self):
        with self.assertRaises(ValueError): self.cargar([{'rol': 2, 'heroe_id': 99, 'dominio': 3}])

    def test_valores_invalidos(self):
        for k, v in [('rol', True), ('rol', 6), ('dominio', 0), ('dominio', True), ('heroe_id', True)]:
            with self.subTest(k=k, v=v), self.assertRaises(ValueError): self.cargar([dict(self.filas[0], **{k: v})])

    def test_esquema(self):
        with self.assertRaises(ValueError): cargar_repertorio({'esquema': 2, 'entradas': []}, catalogo=self.cat)

    def test_sin_preferencias_para_rol(self):
        self.assertEqual(candidatos_personales(self.cargar(self.filas), UltimoPick(True, frozenset({1, 2}), ()), rol=5), ())
