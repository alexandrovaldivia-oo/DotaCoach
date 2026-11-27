"""Filtro conservador para una captura archivada y anotada manualmente.
No captura pantalla ni habilita consejos en vivo. No certifica vetos visuales.
Cada llamada corresponde a una sola captura; no conserva anotaciones previas.
"""
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from .cuadricula import CasillaIdentificada


@dataclass(frozen=True)
class Disponibilidad:
    disponibles: frozenset[int]
    excluidos: frozenset[int]
    desconocidos: frozenset[int]
    incidencias: tuple[str, ...]


def evaluar(resultados, *, catalogo, anotaciones=None, seleccionados=(),
            umbral=.82, margen=.12):
    """Anotaciones humanas de ESTA captura: casilla -> disponible/vetado/seleccionado.
    Una marca probable o dudosa bloquea incluso una anotacion de disponibilidad.
    Seleccionados: IDs confirmados independientemente en la misma captura.
    Sin anotacion positiva, ningun heroe se considera disponible.
    """
    if not isinstance(resultados, Mapping):
        raise ValueError('Resultados invalidos')
    if not all(type(v) in (int, float) and isfinite(v) and 0 < v <= 1
               for v in (umbral, margen)):
        raise ValueError('Umbrales invalidos')
    ids = {h.id for h in catalogo.heroes}
    anotaciones = {} if anotaciones is None else anotaciones
    if (not isinstance(anotaciones, Mapping) or not set(anotaciones) <= set(resultados)
            or any(v not in ('disponible', 'vetado', 'seleccionado') for v in anotaciones.values())):
        raise ValueError('Anotaciones invalidas')
    seleccionados = tuple(seleccionados)
    if any(type(i) is not int or i not in ids for i in seleccionados):
        raise ValueError('Seleccion desconocida')
    validos = {}
    incidencias = []
    for k, r in resultados.items():
        if (not isinstance(r, CasillaIdentificada) or
                r.marca not in ('marca_probable', 'dudosa', 'sin_marca_detectada')):
            raise ValueError('Casilla invalida')
        if r.heroe_id is not None and (type(r.heroe_id) is not int or r.heroe_id not in ids):
            raise ValueError('Identidad fuera del catalogo')
        if not all(type(v) in (int, float) and isfinite(v) for v in (r.similitud, r.margen)):
            raise ValueError('Puntuacion invalida')
        if r.heroe_id is not None and r.similitud >= umbral and r.margen >= margen:
            validos[k] = r
    conteo = Counter(r.heroe_id for r in validos.values())
    disponibles, excluidos = set(), set(seleccionados)
    for k, r in validos.items():
        i, a = r.heroe_id, anotaciones.get(k)
        if conteo[i] > 1:
            incidencias.append('identidad_duplicada:' + str(i))
            continue
        if a in ('vetado', 'seleccionado') or r.marca == 'marca_probable':
            excluidos.add(i)
        if a == 'disponible':
            if i in excluidos or r.marca != 'sin_marca_detectada':
                incidencias.append('disponibilidad_contradictoria:' + str(i))
            else:
                disponibles.add(i)
    disponibles -= excluidos
    return Disponibilidad(frozenset(disponibles), frozenset(excluidos),
                          frozenset(ids - disponibles - excluidos), tuple(sorted(set(incidencias))))
