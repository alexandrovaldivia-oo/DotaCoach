"""Preferencias personales explícitas para análisis offline; no infiere roles ni habilidad."""
from dataclasses import dataclass
from collections.abc import Mapping
from .estado import ROLES
from .ultimo_pick import UltimoPick


@dataclass(frozen=True)
class Preferencia:
    rol: int
    heroe_id: int
    dominio: int


@dataclass(frozen=True)
class Repertorio:
    entradas: tuple[Preferencia, ...]


def cargar_repertorio(datos, *, catalogo):
    """Esquema 1: entradas con rol, heroe_id y dominio declarado de 1 a 3."""
    if (not isinstance(datos, Mapping) or type(datos.get('esquema')) is not int
            or datos['esquema'] != 1 or not isinstance(datos.get('entradas'), list)):
        raise ValueError('Formato de repertorio invalido')
    entradas, vistos = [], set()
    for fila in datos['entradas']:
        if not isinstance(fila, Mapping) or set(fila) != {'rol', 'heroe_id', 'dominio'}:
            raise ValueError('Entrada de repertorio invalida')
        rol, ident, dominio = (fila[k] for k in ('rol', 'heroe_id', 'dominio'))
        if (type(rol) is not int or rol not in ROLES or type(ident) is not int
                or catalogo.por_id(ident) is None or type(dominio) is not int
                or dominio not in (1, 2, 3) or (rol, ident) in vistos):
            raise ValueError('Preferencia invalida o duplicada')
        vistos.add((rol, ident))
        entradas.append(Preferencia(rol, ident, dominio))
    return Repertorio(tuple(sorted(entradas, key=lambda e: (e.rol, -e.dominio, e.heroe_id))))


def candidatos_personales(repertorio, ultimo_pick, *, rol):
    """Filtra candidatos confirmados. El orden refleja dominio, no ventaja estratégica."""
    if (not isinstance(repertorio, Repertorio) or not isinstance(ultimo_pick, UltimoPick)
            or type(rol) is not int or rol not in ROLES):
        raise ValueError('Entradas invalidas')
    if not ultimo_pick.listo or ultimo_pick.motivos:
        return ()
    return tuple(e for e in repertorio.entradas
                 if e.rol == rol and e.heroe_id in ultimo_pick.candidatos)
