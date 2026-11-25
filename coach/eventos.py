"""Detecta que cambio entre dos estados consecutivos."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evento:
    tipo: str
    dato: str = ""
    valor: int = 0


def detectar(prev, act):
    if not act.en_partida:
        return []

    cambio_partida = (
        prev.match_id and act.match_id and prev.match_id != act.match_id
    )
    if not prev.en_partida or cambio_partida:
        return [Evento("inicio", act.heroe)]

    eventos = []
    if act.nivel > prev.nivel:
        eventos.append(Evento("nivel", valor=act.nivel))
    if act.reloj >= 0:
        for item in sorted(act.items - prev.items):
            eventos.append(Evento("item_nuevo", item))
    if act.kills > prev.kills:
        eventos.append(Evento("kill", valor=act.kills - prev.kills))
    if act.deaths > prev.deaths:
        eventos.append(Evento("muerte", valor=act.deaths - prev.deaths))
    if act.racha >= 3 and act.racha > prev.racha:
        eventos.append(Evento("racha", valor=act.racha))
    return eventos
