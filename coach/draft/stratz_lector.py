"""Lectura offline de SQLite existente; no crea ni modifica archivos."""
import math
import sqlite3
from contextlib import closing
from pathlib import Path


def _abrir(ruta):
    return sqlite3.connect(Path(ruta).resolve().as_uri() + '?mode=ro', uri=True)


def intervalo_wilson(v, n):
    """Intervalo binomial aproximado 95%; no mide sesgos ni causalidad."""
    if type(v) is not int or type(n) is not int or not 0 <= v <= n or n == 0:
        raise ValueError('Conteos invalidos')
    p = v/n
    z = 1.959963984540054
    d = 1 + z*z/n
    centro = (p + z*z/(2*n))/d
    radio = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return max(0., centro-radio), min(1., centro+radio)


def consultar(ruta, semana, rango, heroe, relacion, otro, semana_referencia=None):
    if relacion not in ('with', 'vs'):
        raise ValueError('Relacion invalida')
    with closing(_abrir(ruta)) as db:
        fila = db.execute('SELECT partidas,victorias,synergy,rango_devuelto FROM relaciones_v1 WHERE semana=? AND rango_solicitado=? AND heroe=? AND relacion=? AND otro=?', (semana,rango,heroe,relacion,otro)).fetchone()
    if fila is None:
        return None
    n,v,s,etiqueta = fila
    limites = intervalo_wilson(v,n)
    if not math.isfinite(s):
        raise ValueError('Indicador invalido')
    return dict(partidas=n,victorias=v,tasa=v/n,intervalo95=limites,synergy_original=s,rango_solicitado=rango,rango_devuelto=etiqueta,rango_certificado=False,semana=semana,desactualizado=None if semana_referencia is None else semana != semana_referencia)


def auditar(ruta, ids):
    """Comprueba integridad fisica y concordancia de lotes y catalogo."""
    ids = set(ids)
    if len(ids)<2:
        raise ValueError('Catalogo insuficiente')
    with closing(_abrir(ruta)) as db:
        db.execute('BEGIN')
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Integridad SQLite incorrecta')
        lotes = db.execute('SELECT semana,rango,heroe,cantidad FROM lotes_v1 ORDER BY semana,rango,heroe').fetchall()
        filas = db.execute('SELECT semana,rango_solicitado,heroe,relacion,otro,rango_devuelto,partidas,victorias,synergy,base1,base2 FROM relaciones_v1').fetchall()
    grupos = {}
    for w,r,h,rel,o,et,n,v,s,b1,b2 in filas:
        intervalo_wilson(v,n)
        if not isinstance(et,str) or not et or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (s,b1,b2)) or not (0<=b1<=1 and 0<=b2<=1):
            raise ValueError('Metricas invalidas')
        grupo = grupos.setdefault((w,r,h), [])
        grupo.append((rel,o,et))
    if set(grupos) != {(w,r,h) for w,r,h,_ in lotes}:
        raise ValueError('Lotes y relaciones no coinciden')
    resumen=[]
    for w,r,h,n in lotes:
        g=grupos[(w,r,h)]
        esperado={(rel,o) for rel in ('with','vs') for o in ids-{h}}
        if h not in ids or n!=len(g) or len(g)!=len(esperado) or {(rel,o) for rel,o,_ in g}!=esperado:
            raise ValueError('Cobertura o cantidad incorrecta')
        resumen.append(dict(semana=w,rango=r,heroe=h,aliados=sum(rel=='with' for rel,_,_ in g),enemigos=sum(rel=='vs' for rel,_,_ in g),etiquetas=sorted({et for _,_,et in g})))
    return dict(integridad='ok',total=len(filas),lotes=resumen)
