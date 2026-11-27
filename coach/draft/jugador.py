"""Resolución conservadora del equipo y casilla en capturas offline.
Los roles permiten inferir un lado, no la identidad personal. No usa nombres.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from .estado import CASILLAS, LADOS, ROLES
from .roles import RolVisual


@dataclass(frozen=True)
class JugadorDraft:
    lado_probable: str | None
    casilla_propia: str | None
    rol: int | None
    motivo: str


def identificar_jugador(roles, *, casilla_confirmada=None):
    """Una confirmación manual debe pertenecer a la captura analizada.
    Sin confirmación no se deduce la identidad por color, rango o rol.
    Un lado probable requiere los cinco roles únicos y ningún rol opuesto.
    """
    if not isinstance(roles, Mapping) or set(roles) != set(CASILLAS):
        raise ValueError('Se requieren diez casillas')
    for resultado in roles.values():
        if not isinstance(resultado, RolVisual):
            raise ValueError('Resultado de rol invalido')
        if resultado.rol is not None and (type(resultado.rol) is not int or resultado.rol not in ROLES):
            raise ValueError('Rol invalido')
    if casilla_confirmada is not None and casilla_confirmada not in CASILLAS:
        raise ValueError('Casilla invalida')
    grupos = {lado: [roles[c].rol for c in CASILLAS if c.startswith(lado + '_')] for lado in LADOS}
    candidatos = [lado for lado in LADOS if set(grupos[lado]) == set(ROLES)
                  and all(r is None for r in grupos[LADOS[1-LADOS.index(lado)]])]
    lado = next(iter(candidatos), None)
    if lado is None:
        return JugadorDraft(None, None, None, 'equipo_no_concluyente')
    if casilla_confirmada is None:
        return JugadorDraft(lado, None, None, 'falta_confirmar_casilla')
    if not casilla_confirmada.startswith(lado + '_'):
        return JugadorDraft(lado, None, None, 'casilla_contradictoria')
    return JugadorDraft(lado, casilla_confirmada, roles[casilla_confirmada].rol, 'casilla_confirmada_manualmente')
