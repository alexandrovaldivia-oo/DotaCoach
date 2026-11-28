"""Contexto de estudio archivado; sin captura, red ni acciones sobre Dota."""
from dataclasses import dataclass, replace
import re
import unicodedata
from statistics import mean
from .analisis_offline import PERFILES
from .capacidades import validar_perfiles, consultar as perfil
from .stratz_lector import consultar as estadistica


def normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', texto.casefold()) if not unicodedata.combining(c)).split())


def resolver(catalogo, nombre):
    clave = normalizar(nombre)
    alias = {'qop': 'queen of pain', 'sb': 'spirit breaker'}
    clave = alias.get(clave, clave)
    encontrados = [h.id for h in catalogo.heroes if normalizar(h.nombre) == clave or normalizar(h.clave.removeprefix('npc_dota_hero_').replace('_',' ')) == clave]
    if len(encontrados) != 1:
        raise ValueError('Nombre desconocido o ambiguo: '+nombre)
    return encontrados[0]


@dataclass(frozen=True)
class Contexto:
    rol: int = 2
    aliados: tuple = ()
    enemigos: tuple = ()
    vetados: tuple = ()
    candidatos: tuple = ()
    roles_declarados: tuple = ()
    archivado: bool = False
    fase: int | None = None


def validar(c, catalogo):
    if c.archivado is not True or type(c.rol) is not int or c.rol not in range(1,6):
        raise ValueError('Solo estudio archivado con posicion valida')
    if c.fase is not None and (type(c.fase) is not int or c.fase not in (1, 2, 3)):
        raise ValueError('Fase declarada inválida')
    grupos = (c.aliados,c.enemigos,c.vetados,c.candidatos)
    if any(not isinstance(g,tuple) for g in grupos):
        raise ValueError('Listas invalidas')
    ids = sum(grupos, ())
    if len(c.aliados)>4 or len(c.enemigos)>5 or len(ids)!=len(set(ids)) or any(catalogo.por_id(i) is None for i in ids):
        raise ValueError('Selecciones contradictorias o desconocidas')
    vistos = set()
    for h,r in c.roles_declarados:
        if h not in c.aliados or h in vistos or type(r) is not int or r not in range(1,6):
            raise ValueError('Rol declarado invalido')
        vistos.add(h)
    return c


def actualizar(c, texto, catalogo):
    """Comandos de texto explicitos; no interpreta lenguaje libre ni adivina nombres."""
    validar(c,catalogo)
    texto = texto.strip()
    m = re.fullmatch(r'(?:soy|juego de)\s+(mid|carry|off|offlane|[1-5])', normalizar(texto))
    if m:
        roles={'mid':2,'carry':1,'off':3,'offlane':3}
        v=m[1]; nuevo=replace(c,rol=roles[v] if v in roles else int(v))
    elif (m:=re.fullmatch(r'(?:mi\s+)?(.+?)\s+(?:es|juega de|esta jugando de)\s+(?:posicion\s+)?([1-5])',normalizar(texto))):
        h=resolver(catalogo,m[1]); roles=dict(c.roles_declarados); roles[h]=int(m[2]); nuevo=replace(c,roles_declarados=tuple(roles.items()))
    elif ':' in texto:
        campo, valores = texto.split(':',1)
        campo=normalizar(campo)
        if campo not in ('aliados','enemigos','vetados','candidatos'):
            raise ValueError('Campo desconocido')
        ids=tuple(resolver(catalogo,x.strip()) for x in valores.split(',') if x.strip())
        nuevo=replace(c,**{campo:ids})
        if campo=='aliados': nuevo=replace(nuevo,roles_declarados=tuple((h,r) for h,r in c.roles_declarados if h in ids))
    else:
        raise ValueError('Usa Soy mid, Aliados: Lion, Axe, o Mi Axe juega de 5')
    return validar(nuevo,catalogo)


def analizar(c, *, catalogo, repertorio, ruta, semana, rango, minimo=100):
    validar(c,catalogo)
    if type(minimo) is not int or minimo<1 or type(semana) is not int or semana<1 or not isinstance(rango,str) or not rango.strip():
        raise ValueError('Parametros estadisticos invalidos')
    perfiles=validar_perfiles(PERFILES,catalogo)
    propios={e.heroe_id for e in repertorio.entradas if e.rol==c.rol}
    total=len(c.aliados)+len(c.enemigos)
    filas=[]
    for h in c.candidatos:
        datos=[estadistica(ruta,semana,rango,h,t,o) for t,g in [('with',c.aliados),('vs',c.enemigos)] for o in g]
        suficientes=[d for d in datos if d is not None and d['partidas']>=minimo]
        filas.append(dict(nombre=catalogo.por_id(h).nombre,heroe=h,personal=h in propios,conocidas=total,suficientes=len(suficientes),media=mean(d['tasa'] for d in suficientes) if total and len(suficientes)==total else None,evidencias=perfil(perfiles,catalogo,h).evidencias))
    return dict(rol=c.rol,filas=tuple(filas),roles_declarados=c.roles_declarados,meta_verificado=False,recomendacion_disponible=False,advertencia='Rango y vigencia no certificados. Solo estudio offline. Sin estadisticas verificadas por posicion.')
