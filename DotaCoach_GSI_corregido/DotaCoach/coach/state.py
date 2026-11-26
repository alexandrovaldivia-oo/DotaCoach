"""Modelo del estado de la partida, construido a partir del JSON de GSI.
Todo es tolerante: si un campo no llega, se usa un valor por defecto."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EstadoPartida:
    en_partida: bool = False
    fase: str = ""
    reloj: int = 0
    match_id: str = ""
    heroe: str = ""
    nivel: int = 0
    vivo: bool = True
    oro: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    racha: int = 0
    items: frozenset = frozenset()
    habilidades: tuple = ()

    @property
    def minuto(self):
        return max(self.reloj, 0) // 60


def _entero(valor, defecto=0):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _bloque(payload, nombre):
    dato = payload.get(nombre)
    return dato if isinstance(dato, dict) else {}


def _nombres_items(bloque):
    # Limitacion: dos copias del mismo objeto cuentan como una.
    nombres = set()
    for clave, dato in bloque.items():
        if clave.startswith("slot") or clave.startswith("stash"):
            nombre = dato.get("name") if isinstance(dato, dict) else None
            if nombre and nombre != "empty":
                nombres.add(nombre)
    return frozenset(nombres)


def _habilidades(bloque):
    lista = []
    for clave in sorted(bloque.keys()):
        dato = bloque.get(clave)
        if clave.startswith("ability") and isinstance(dato, dict):
            lista.append((str(dato.get("name", "")), _entero(dato.get("level"))))
    return tuple(lista)


def parsear(payload):
    if not isinstance(payload, dict):
        return EstadoPartida()

    mapa = _bloque(payload, "map")
    hero = _bloque(payload, "hero")
    player = _bloque(payload, "player")

    nombre = str(hero.get("name", "")).replace("npc_dota_hero_", "")
    nivel = _entero(hero.get("level"))

    return EstadoPartida(
        en_partida=bool(nombre) and nivel > 0,
        fase=str(mapa.get("game_state", "")),
        reloj=_entero(mapa.get("clock_time")),
        match_id=str(mapa.get("matchid", "")),
        heroe=nombre,
        nivel=nivel,
        vivo=bool(hero.get("alive", True)),
        oro=_entero(player.get("gold")),
        kills=_entero(player.get("kills")),
        deaths=_entero(player.get("deaths")),
        assists=_entero(player.get("assists")),
        racha=_entero(player.get("kill_streak")),
        items=_nombres_items(_bloque(payload, "items")),
        habilidades=_habilidades(_bloque(payload, "abilities")),
    )
