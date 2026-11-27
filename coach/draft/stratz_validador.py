"""Validacion estricta; el rango devuelto no se corrige ni se infiere."""
import math
from .stratz_cliente import RANGOS


def validar(grupo, heroe, rango, catalogo_ids, semana=None):
    ids = set(catalogo_ids)
    if rango not in RANGOS or heroe not in ids or grupo.get('heroId') != heroe:
        raise ValueError('Origen invalido')
    filas, periodos = [], set()
    for relacion in ('with', 'vs'):
        vistos = set()
        datos = grupo.get(relacion)
        if not isinstance(datos, list):
            raise ValueError('Lista ausente')
        for fila in datos:
            if not isinstance(fila, dict):
                raise ValueError('Fila invalida')
            a,b,w,n,v = (fila.get(k) for k in ('heroId1','heroId2','week','matchCount','winCount'))
            if (any(type(x) is not int for x in (a,b,w,n,v)) or a != heroe
                or b not in ids - {heroe} or b in vistos or w <= 0 or n <= 0 or not 0 <= v <= n):
                raise ValueError('Relacion invalida o duplicada')
            etiqueta = fila.get('bracketBasicIds')
            if not isinstance(etiqueta, str) or not etiqueta:
                raise ValueError('Etiqueta ausente')
            for k in ('synergy','winRateHeroId1','winRateHeroId2','winsAverage'):
                x = fila.get(k)
                if type(x) not in (int,float) or not math.isfinite(x):
                    raise ValueError('Metrica invalida')
                if k != 'synergy' and not 0 <= x <= 1:
                    raise ValueError('Tasa invalida')
            if abs(fila['winsAverage'] - v/n) > .00051:
                raise ValueError('Tasa incoherente')
            vistos.add(b); periodos.add(w)
            filas.append((relacion, b, etiqueta, n, v, fila['synergy'], fila['winRateHeroId1'], fila['winRateHeroId2']))
        if vistos != ids - {heroe}:
            raise ValueError('Cobertura incompleta')
    if len(periodos) != 1 or (semana is not None and periodos != {semana}):
        raise ValueError('Periodo inconsistente')
    return next(iter(periodos)), filas
