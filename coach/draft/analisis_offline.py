"""Comparacion explicable de escenarios archivados; sin red ni integracion en partida."""
from .capacidades import CAPACIDADES, PILOTO, Perfil, Evidencia, validar_perfiles, consultar
from .stratz_lector import consultar as estadistica
from .repertorio import Repertorio
from .ultimo_pick import UltimoPick


def _e(capacidad, estado, detalle, slug):
    return Evidencia(capacidad, estado, detalle, 'https://www.dota2.com/hero/'+slug, '2026-11-27')

PERFILES = PILOTO + (
    Perfil(87, (_e('silencio','documentado','Su tormenta estatica silencia enemigos en su area.','disruptor'),)),
    Perfil(100, (_e('aturdimiento','condicional','La bola de nieve puede aturdir al impactar.','tusk'),)),
    Perfil(8, (_e('proteccion','inferido','Su guardian de curacion puede ayudar a mantener vivos a aliados cercanos.','juggernaut'),)),
)


def comparar(*, catalogo, repertorio, ultimo_pick, aliados, enemigos, rol, ruta, semana, rango, modo='equilibrado'):
    """Orden alfabetico, no ranking. No convierte falta de evidencia en cero."""
    if not isinstance(ultimo_pick, UltimoPick) or not ultimo_pick.listo or ultimo_pick.motivos:
        raise ValueError('Escenario no confirmado')
    if not isinstance(repertorio, Repertorio) or type(rol) is not int or rol not in range(1,6):
        raise ValueError('Repertorio o posicion invalida')
    if modo not in ('personal','estrategico','equilibrado'):
        raise ValueError('Modo invalido')
    if type(semana) is not int or semana <= 0 or not isinstance(rango,str) or not rango.strip():
        raise ValueError('Periodo o rango invalido')
    aliados, enemigos = tuple(aliados), tuple(enemigos)
    if len(aliados)!=4 or len(enemigos)!=4 or len(set(aliados+enemigos))!=8:
        raise ValueError('Escenario archivado incompleto')
    ids = set(ultimo_pick.candidatos)
    if not ids or ids.intersection(aliados+enemigos) or any(catalogo.por_id(i) is None for i in ids.union(aliados+enemigos)):
        raise ValueError('Identidades o disponibilidad invalidas')
    perfiles = validar_perfiles(PERFILES,catalogo)
    personales = {e.heroe_id:e for e in repertorio.entradas if e.rol==rol}
    if modo=='personal': ids.intersection_update(personales)
    cobertura = {c: tuple((i, consultar(perfiles,catalogo,i).estado(c)) for i in aliados
                           if consultar(perfiles,catalogo,i).estado(c)!='desconocido') for c in sorted(CAPACIDADES)}
    filas=[]
    for i in sorted(ids,key=lambda i:(catalogo.por_id(i).nombre.casefold(),i)):
        perfil=consultar(perfiles,catalogo,i)
        relaciones=tuple((rel,j,estadistica(ruta,semana,rango,i,rel,j)) for rel,equipo in (('with',aliados),('vs',enemigos)) for j in equipo)
        preferencia=personales.get(i)
        filas.append(dict(heroe=i,nombre=catalogo.por_id(i).nombre,en_repertorio=preferencia is not None,
                          dominio=preferencia.dominio if preferencia else None,
                          evidencias=perfil.evidencias, aportes_sin_evidencia_previa=tuple(e.capacidad for e in perfil.evidencias if not cobertura[e.capacidad]),
                          relaciones=relaciones, relaciones_presentes=sum(d is not None for _,_,d in relaciones)))
    return dict(modo=modo, rol=rol, cobertura=cobertura, candidatos=tuple(filas), ranking_disponible=False,
                advertencias=('Fuera de partida.','Capacidad no documentada no implica ausencia.', 'Rango y vigencia no certificados.', 'Preferencia personal no implica idoneidad por posicion.', 'Sin puntuacion global ni recomendacion definitiva.'))
