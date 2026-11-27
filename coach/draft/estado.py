"""Estado de draft para análisis offline. No infiere vetos, roles ni confirmaciones.
Las anotaciones humanas corresponden a una sola captura, no se arrastran.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from .reconocimiento import Coincidencia

LADOS = ('izquierda', 'derecha')
CASILLAS = tuple(f'{lado}_{i}' for lado in LADOS for i in range(1, 6))
ROLES = (1, 2, 3, 4, 5)

@dataclass(frozen=True)
class EstadoDraft:
    aliados: tuple[str, ...]
    enemigos: tuple[str, ...]
    vetados: frozenset[str] | None
    rol: int | None
    lado_propio: str | None
    incidencias: tuple[str, ...]
    listo_ultimo_pick: bool


def interpretar(coincidencias, *, catalogo, lado_propio=None, casilla_propia=None,
                confirmadas=(), vacias=(), vetados=None, rol=None,
                turno_propio_confirmado=False):
    """Solo usa identidades reconocidas y confirmaciones visibles explícitas.

    catalogo: CatalogoHeroes; confirmadas/vacias: nombres de casillas anotadas
    en esta captura; vetados: claves cortas, None si lista no comprobada.
    El turno y el rol se anotan manualmente; no se predice el orden de picks.
    """
    if not isinstance(coincidencias, Mapping) or set(coincidencias) != set(CASILLAS):
        raise ValueError('Se requieren las diez casillas')
    if lado_propio is not None and lado_propio not in LADOS:
        raise ValueError('Lado invalido')
    if casilla_propia is not None and (casilla_propia not in CASILLAS or lado_propio is None or not casilla_propia.startswith(lado_propio + '_')):
        raise ValueError('Casilla propia incompatible')
    if rol is not None and (type(rol) is not int or rol not in ROLES):
        raise ValueError('Rol invalido')
    confirmadas, vacias = set(confirmadas), set(vacias)
    if not (confirmadas | vacias) <= set(CASILLAS) or confirmadas & vacias:
        raise ValueError('Anotaciones incompatibles')
    def existe(clave):
        return isinstance(clave, str) and catalogo.por_clave('npc_dota_hero_' + clave) is not None
    if vetados is not None:
        if isinstance(vetados, str):
            raise ValueError('Lista de vetos invalida')
        vetados = frozenset(vetados)
        if not all(existe(h) for h in vetados):
            raise ValueError('Veto desconocido')
    incidencias, grupos = [], {lado: [] for lado in LADOS}
    identidades = []
    for casilla in CASILLAS:
        c = coincidencias[casilla]
        if not isinstance(c, Coincidencia):
            raise ValueError('Coincidencia invalida')
        if casilla in vacias and c.heroe is not None:
            incidencias.append('vacia_con_retrato:' + casilla)
        if casilla not in confirmadas:
            continue
        if not existe(c.heroe):
            incidencias.append('identidad_desconocida:' + casilla)
            continue
        grupos[casilla.split('_')[0]].append(c.heroe)
        identidades.append(c.heroe)
    if len(set(identidades)) != len(identidades):
        incidencias.append('heroes_duplicados')
    if vetados is not None and set(identidades) & vetados:
        incidencias.append('seleccion_vetada')
    if lado_propio is None:
        aliados = enemigos = ()
    else:
        aliados = tuple(grupos[lado_propio])
        enemigos = tuple(grupos['derecha' if lado_propio == 'izquierda' else 'izquierda'])
    listo = (not incidencias and lado_propio is not None and rol is not None
             and vetados is not None and casilla_propia in vacias
             and turno_propio_confirmado is True and len(aliados) == len(enemigos) == 4
             and len(confirmadas) == 8 and len(vacias) == 2)
    return EstadoDraft(aliados, enemigos, vetados, rol, lado_propio,
                       tuple(incidencias), listo)
