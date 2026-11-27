import unittest
from dataclasses import replace
from coach.datos.catalogo_heroes import CatalogoHeroes, Heroe
from coach.draft.estado import EstadoDraft
from coach.draft.jugador import JugadorDraft
from coach.draft.disponibilidad import Disponibilidad
from coach.draft.ultimo_pick import evaluar_ultimo_pick


class TestUltimoPick(unittest.TestCase):
    def setUp(self):
        self.cat = CatalogoHeroes(Heroe(i, 'npc_dota_hero_h'+str(i), str(i), 0, 1) for i in range(1, 13))
        self.e = EstadoDraft(tuple('h'+str(i) for i in range(1,5)), tuple('h'+str(i) for i in range(5,9)), frozenset(('h9',)), 2, 'izquierda', (), True)
        self.j = JugadorDraft('izquierda','izquierda_5',2,'casilla_confirmada_manualmente')
        self.d = Disponibilidad(frozenset((10,)),frozenset(range(1,10)),frozenset((11,12)),())
    def evaluar(self, **kw):
        args = dict(estado=self.e,jugador=self.j,disponibilidad=self.d,catalogo=self.cat,fase_confirmada=True,turno_confirmado=True)
        return evaluar_ultimo_pick(**(args | kw))
    def test_listo(self):
        r=self.evaluar(); self.assertTrue(r.listo); self.assertEqual(r.candidatos,frozenset((10,)))
    def test_fase(self): self.assertFalse(self.evaluar(fase_confirmada=False).listo)
    def test_turno(self): self.assertFalse(self.evaluar(turno_confirmado=False).listo)
    def test_casilla(self): self.assertFalse(self.evaluar(jugador=replace(self.j,casilla_propia=None)).listo)
    def test_rol(self): self.assertFalse(self.evaluar(jugador=replace(self.j,rol=3)).listo)
    def test_incompleto(self): self.assertFalse(self.evaluar(estado=replace(self.e,enemigos=('h5',))).listo)
    def test_vetos(self): self.assertFalse(self.evaluar(estado=replace(self.e,vetados=None)).listo)
    def test_bloqueado(self):
        d=replace(self.d,disponibles=frozenset((9,10)),excluidos=frozenset(range(1,9)))
        self.assertFalse(self.evaluar(disponibilidad=d).listo)
    def test_sin_candidatos(self):
        d=replace(self.d,disponibles=frozenset(),desconocidos=frozenset((10,11,12)))
        self.assertFalse(self.evaluar(disponibilidad=d).listo)
    def test_particion(self):
        with self.assertRaises(ValueError): self.evaluar(disponibilidad=replace(self.d,desconocidos=frozenset((10,11,12))))
