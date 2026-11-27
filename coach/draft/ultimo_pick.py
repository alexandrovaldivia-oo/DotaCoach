"""Validación offline del último pick. No captura ni activa asistencia en vivo."""
from dataclasses import dataclass
from .estado import EstadoDraft, LADOS, CASILLAS, ROLES
from .jugador import JugadorDraft
from .disponibilidad import Disponibilidad


@dataclass(frozen=True)
class UltimoPick:
    listo: bool
    candidatos: frozenset[int]
    motivos: tuple[str, ...]


def evaluar_ultimo_pick(estado, jugador, disponibilidad, *, catalogo,
                        fase_confirmada=False, turno_confirmado=False):
    """Todas las entradas deben corresponder a la misma captura archivada.

    Fase y turno son anotaciones humanas, no inferencias por temporizador.
    No convierte una lista parcial de vetos en una lista completa.
    """
    if not isinstance(estado, EstadoDraft) or not isinstance(jugador, JugadorDraft) or not isinstance(disponibilidad, Disponibilidad):
        raise ValueError('Entradas invalidas')
    if type(fase_confirmada) is not bool or type(turno_confirmado) is not bool:
        raise ValueError('Confirmaciones invalidas')
    ids = {h.id for h in catalogo.heroes}
    grupos = (disponibilidad.disponibles, disponibilidad.excluidos, disponibilidad.desconocidos)
    if any(not isinstance(g, frozenset) or any(type(i) is not int or i not in ids for i in g) for g in grupos):
        raise ValueError('Disponibilidad invalida')
    if set.union(*(set(g) for g in grupos)) != ids or any(a & b for i, a in enumerate(grupos) for b in grupos[i+1:]):
        raise ValueError('Particion de disponibilidad invalida')
    motivos = []
    if not fase_confirmada: motivos.append('fase_no_confirmada')
    if not turno_confirmado: motivos.append('turno_no_confirmado')
    if not estado.listo_ultimo_pick or estado.incidencias: motivos.append('estado_no_listo')
    if (jugador.lado_probable not in LADOS or jugador.casilla_propia not in CASILLAS
            or not jugador.casilla_propia.startswith(jugador.lado_probable + '_')
            or jugador.lado_probable != estado.lado_propio or type(jugador.rol) is not int
            or jugador.rol not in ROLES or jugador.rol != estado.rol
            or jugador.motivo != 'casilla_confirmada_manualmente'):
        motivos.append('jugador_no_confirmado')
    seleccion = estado.aliados + estado.enemigos
    if len(estado.aliados) != 4 or len(estado.enemigos) != 4 or len(set(seleccion)) != 8:
        motivos.append('selecciones_incompletas_o_duplicadas')
    if estado.vetados is None: motivos.append('vetos_no_confirmados')
    vetos = estado.vetados or frozenset()
    if set(seleccion) & vetos: motivos.append('seleccion_vetada')
    bloqueados = set()
    for clave in set(seleccion) | vetos:
        heroe = catalogo.por_clave('npc_dota_hero_' + clave)
        if heroe is None: motivos.append('identidad_desconocida')
        else: bloqueados.add(heroe.id)
    if disponibilidad.incidencias: motivos.append('disponibilidad_contradictoria')
    if bloqueados & disponibilidad.disponibles: motivos.append('candidato_bloqueado')
    candidatos = disponibilidad.disponibles - bloqueados
    if not candidatos: motivos.append('sin_candidatos_confirmados')
    return UltimoPick(not motivos, frozenset() if motivos else candidatos, tuple(dict.fromkeys(motivos)))
