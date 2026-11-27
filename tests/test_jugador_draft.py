import unittest
from coach.draft.estado import CASILLAS
from coach.draft.roles import RolVisual
from coach.draft.jugador import identificar_jugador


def muestra(lado='izquierda'):
    return {c: RolVisual(int(c.split('_')[-1]) if c.startswith(lado+'_') else None, .9, .2) for c in CASILLAS}


class TestJugadorDraft(unittest.TestCase):
    def test_lado_izquierdo(self):
        self.assertEqual(identificar_jugador(muestra()).lado_probable, 'izquierda')
    def test_lado_derecho(self):
        self.assertEqual(identificar_jugador(muestra('derecha')).lado_probable, 'derecha')
    def test_no_adivina_casilla(self):
        r = identificar_jugador(muestra())
        self.assertIsNone(r.casilla_propia)
        self.assertIsNone(r.rol)
    def test_confirmacion(self):
        r = identificar_jugador(muestra(), casilla_confirmada='izquierda_2')
        self.assertEqual((r.casilla_propia,r.rol), ('izquierda_2',2))
    def test_contradiccion(self):
        self.assertIsNone(identificar_jugador(muestra(), casilla_confirmada='derecha_2').casilla_propia)
    def test_rol_faltante(self):
        d=muestra(); d['izquierda_1']=RolVisual(None,0,0)
        self.assertIsNone(identificar_jugador(d).lado_probable)
    def test_rol_duplicado(self):
        d=muestra(); d['izquierda_1']=d['izquierda_2']
        self.assertIsNone(identificar_jugador(d).lado_probable)
    def test_rol_opuesto(self):
        d=muestra(); d['derecha_1']=d['izquierda_1']
        self.assertIsNone(identificar_jugador(d).lado_probable)
    def test_entrada_invalida(self):
        with self.assertRaises(ValueError): identificar_jugador({})
        with self.assertRaises(ValueError): identificar_jugador(muestra(), casilla_confirmada='otra')
    def test_no_arrastra_confirmacion(self):
        d=muestra(); identificar_jugador(d, casilla_confirmada='izquierda_2')
        self.assertIsNone(identificar_jugador(d).casilla_propia)
