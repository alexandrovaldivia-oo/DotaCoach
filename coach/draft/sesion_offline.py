"""Integración de escenarios manuales archivados; sin captura, red ni consejos en vivo."""
from .estado import EstadoDraft
from .jugador import JugadorDraft
from .disponibilidad import Disponibilidad
from .ultimo_pick import evaluar_ultimo_pick
from .clasificacion_offline import clasificar
from .stratz_lector import auditar


def analizar_sesion(*, catalogo, repertorio, ruta, semana, rango, rol,
                    aliados, enemigos, vetados, disponibles,
                    archivado=False, fase_confirmada=False, turno_confirmado=False,
                    modo='equilibrado'):
    if archivado is not True or fase_confirmada is not True or turno_confirmado is not True:
        raise ValueError('Solo escenarios archivados con fase y turno confirmados')
    if type(rol) is not int or rol not in range(1, 6):
        raise ValueError('Posicion invalida')
    ids = {h.id for h in catalogo.heroes}
    grupos = (aliados, enemigos, vetados, disponibles)
    if any(not isinstance(g, (list, tuple)) for g in grupos):
        raise ValueError('Se requieren listas explicitas, incluidos los vetos')
    a, e, v, d = map(tuple, grupos)
    todos = a+e+v+d
    if any(type(i) is not int or i not in ids for i in todos):
        raise ValueError('Heroe desconocido')
    if len(a)!=4 or len(e)!=4 or not d or len(set(todos))!=len(todos):
        raise ValueError('Selecciones incompletas, duplicadas o contradictorias')
    def claves(g):
        return tuple(catalogo.por_id(i).clave.removeprefix('npc_dota_hero_') for i in g)
    # Lado y casilla son una representación sintética del escenario manual,
    # no una identificación visual del jugador real.
    estado = EstadoDraft(claves(a), claves(e), frozenset(claves(v)), rol, 'izquierda', (), True)
    jugador = JugadorDraft('izquierda', 'izquierda_5', rol, 'casilla_confirmada_manualmente')
    excluidos = frozenset(a+e+v)
    disponibilidad = Disponibilidad(frozenset(d), excluidos, frozenset(ids-set(todos)), ())
    ultimo = evaluar_ultimo_pick(estado, jugador, disponibilidad, catalogo=catalogo,
                                 fase_confirmada=True, turno_confirmado=True)
    if not ultimo.listo:
        raise ValueError('Escenario rechazado: '+', '.join(ultimo.motivos))
    auditoria = auditar(ruta, ids)
    if not any(l['semana']==semana and l['rango']==rango for l in auditoria['lotes']):
        raise ValueError('Periodo o rango solicitado sin datos locales')
    return clasificar(catalogo=catalogo, repertorio=repertorio, ultimo_pick=ultimo,
                      aliados=a, enemigos=e, rol=rol, ruta=ruta, semana=semana,
                      rango=rango, modo=modo)
