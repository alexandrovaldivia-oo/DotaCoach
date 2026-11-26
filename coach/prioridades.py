"""Selector experimental de avisos. Sin voz, red, hilos ni cola de mensajes.
El llamador debe serializar las llamadas y pasar un reloj monotónico en segundos.
La habilitación de práctica debe ser explícita; no se infiere de GSI.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Intervencion:
    tipo: str
    prioridad: int
    usa_ia: bool = False
    valor: int = 0


# tipo: (prioridad, intervalo por tipo, usa IA)
POLITICA = {
    'vida_baja': (3, 20, False),
    'mana_baja': (2, 30, False),
    'muerte': (2, 30, True),
    'definitiva_disponible': (1, 40, False),
    'item_incorporado': (1, 45, True),
    'racha': (0, 60, True),
}


class ControlAvisos:
    def __init__(self):
        self._sesion = None
        self._ultimo = None
        self._ultima_ia = None
        self._por_tipo = {}
        self._reloj = None
        self._vida_armada = True
        self._mana_armada = True
        self._muerte_vista = None

    def seleccionar(self, eventos, estado, ahora, *, practica=False,
                     ia_disponible=False, ia_ocupada=True):
        """Devuelve a lo sumo una intervención; descarta el resto sin reintentos.
        Los intervalos son reservas de selección, no confirmaciones de reproducción.
        """
        if type(ahora) not in (int, float) or not math.isfinite(ahora):
            raise ValueError('Reloj monotónico inválido')
        if self._reloj is not None and ahora < self._reloj:
            raise ValueError('El reloj monotónico retrocedió')
        self._reloj = ahora
        if practica is not True or not estado.match_id or not estado.heroe:
            return None
        sesion = (estado.match_id, estado.heroe)
        if sesion != self._sesion:
            self._sesion = sesion
            self._por_tipo.clear()
            self._vida_armada = self._mana_armada = True
            self._muerte_vista = None
            # Los límites globales sobreviven al cambio de partida.
        if not estado.en_partida or not estado.fase_activa or estado.pausa is not False:
            return None
        if 'hero.alive' not in estado.conocidos:
            return None
        if estado.vida_porcentaje is not None and estado.vida_porcentaje >= 35:
            self._vida_armada = True
        if estado.mana_porcentaje is not None and estado.mana_porcentaje >= 30:
            self._mana_armada = True
        candidatos = {}
        for e in eventos:
            if e.tipo not in POLITICA:
                continue
            if e.tipo == 'muerte':
                # Dos señales de la misma muerte pueden llegar en POST separados.
                # Ventana conservadora: también puede suprimir una segunda muerte real.
                if self._muerte_vista is not None and ahora-self._muerte_vista < 30:
                    continue
                if estado.vivo:
                    continue
                self._muerte_vista = ahora
            elif not estado.vivo:
                continue
            if e.tipo == 'vida_baja':
                if not self._vida_armada or estado.vida_porcentaje is None or not 0 < estado.vida_porcentaje <= 25:
                    continue
                self._vida_armada = False
            if e.tipo == 'mana_baja':
                if not self._mana_armada or estado.mana_porcentaje is None or estado.mana_porcentaje > 20:
                    continue
                self._mana_armada = False
            prioridad, intervalo, usa_ia = POLITICA[e.tipo]
            if e.tipo in self._por_tipo and ahora-self._por_tipo[e.tipo] < intervalo:
                continue
            if usa_ia and (ia_disponible is not True or ia_ocupada is not False or
                           (self._ultima_ia is not None and ahora-self._ultima_ia < 25)):
                continue
            if e.tipo not in candidatos or e.valor > candidatos[e.tipo].valor:
                candidatos[e.tipo] = Intervencion(e.tipo, prioridad, usa_ia, e.valor)
        if self._ultimo is not None and ahora-self._ultimo < 6:
            return None
        if not candidatos:
            return None
        elegido = sorted(candidatos.values(), key=lambda e: (-e.prioridad, e.usa_ia, e.tipo))[0]
        self._ultimo = self._por_tipo[elegido.tipo] = ahora
        if elegido.usa_ia:
            self._ultima_ia = ahora
        return elegido
