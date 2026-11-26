"""Modelo del estado de la partida, construido a partir del JSON de GSI.
La interfaz antigua conserva sus valores por defecto; los campos nuevos usan None
para datos ausentes o invalidos. No se conserva informacion de mensajes anteriores."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Habilidad:
    casilla: str
    nombre: str | None = None
    nivel: int | None = None
    disponible: bool | None = None
    activa: bool | None = None
    pasiva: bool | None = None
    definitiva: bool | None = None
    recarga: int | None = None
    recarga_maxima: int | None = None
    cargas: int | None = None
    cargas_maximas: int | None = None
    recarga_carga: int | None = None


@dataclass(frozen=True)
class Objeto:
    casilla: str
    nombre: str | None = None
    disponible: bool | None = None
    pasivo: bool | None = None
    nivel: int | None = None
    recarga: int | None = None
    recarga_maxima: int | None = None
    cargas: int | None = None
    cargas_item: int | None = None

    @property
    def vacio(self):
        return None if self.nombre is None else self.nombre == "empty"


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

    # Campos nuevos: None indica ausencia o valor invalido.
    conocidos: frozenset = frozenset()
    invalidos: frozenset = frozenset()
    vida: int | None = None
    vida_maxima: int | None = None
    vida_porcentaje: int | None = None
    mana: int | None = None
    mana_maximo: int | None = None
    mana_porcentaje: int | None = None
    experiencia: int | None = None
    reaparicion: int | None = None
    recompra_coste: int | None = None
    recompra_recarga: int | None = None
    ultimos_golpes: int | None = None
    denegaciones: int | None = None
    gpm: int | None = None
    xpm: int | None = None
    x: int | None = None
    y: int | None = None
    pausa: bool | None = None
    dia: bool | None = None
    radiant: int | None = None
    dire: int | None = None
    equipo: str | None = None
    estados: tuple = ()
    inventario: tuple[Objeto, ...] = ()
    detalle_habilidades: tuple[Habilidad, ...] = ()

    @property
    def fase_activa(self):
        return self.fase == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"

    @property
    def minuto(self):
        return max(self.reloj, 0) // 60


def _numero(valor):
    if type(valor) is int:
        return valor
    if isinstance(valor, str):
        try:
            return int(valor)
        except ValueError:
            pass
    return None


def _entero(valor, defecto=0):
    numero = _numero(valor)
    return defecto if numero is None else numero


def _booleano(valor):
    return valor if type(valor) is bool else None


def _texto(valor):
    return valor if isinstance(valor, str) and valor.strip() else None


def _natural(valor):
    n = _numero(valor)
    return n if n is not None and n >= 0 else None


def _porcentaje(valor):
    n = _natural(valor)
    return n if n is not None and n <= 100 else None


def _bloque(payload, nombre):
    dato = payload.get(nombre)
    return dato if isinstance(dato, dict) else {}


def _nombres_items(bloque):
    # Limitacion: dos copias del mismo objeto cuentan como una.
    nombres = set()
    for clave, dato in bloque.items():
        if clave.startswith("slot") or clave.startswith("stash"):
            nombre = dato.get("name") if isinstance(dato, dict) else None
            if isinstance(nombre, str) and nombre and nombre != "empty":
                nombres.add(nombre)
    return frozenset(nombres)


def _habilidades(bloque):
    lista = []
    for clave in sorted(bloque.keys()):
        dato = bloque.get(clave)
        if clave.startswith("ability") and isinstance(dato, dict):
            lista.append((_texto(dato.get("name")) or "", _entero(dato.get("level"))))
    return tuple(lista)


def parsear(payload):
    if not isinstance(payload, dict):
        return EstadoPartida()

    mapa = _bloque(payload, "map")
    hero = _bloque(payload, "hero")
    player = _bloque(payload, "player")

    conocidos, invalidos = set(), set()

    def leer(bloque, prefijo, clave, convertir):
        ruta = prefijo + "." + clave
        if clave not in bloque:
            return None
        valor = convertir(bloque.get(clave))
        (conocidos if valor is not None else invalidos).add(ruta)
        return valor

    def h(clave, convertir=_natural):
        return leer(hero, "hero", clave, convertir)

    def j(clave, convertir=_natural):
        return leer(player, "player", clave, convertir)

    def m(clave, convertir=_natural):
        return leer(mapa, "map", clave, convertir)

    nombre = (h("name", _texto) or "").removeprefix("npc_dota_hero_")
    nivel = h("level") or 0
    vivo = h("alive", _booleano)
    fase = m("game_state", _texto) or ""
    reloj = m("clock_time", _numero)
    match_id = m("matchid", _texto) or ""
    oro, kills, deaths, assists, racha = (j(k) for k in ("gold", "kills", "deaths", "assists", "kill_streak"))
    campos = dict(
        vida=h("health"), vida_maxima=h("max_health"), vida_porcentaje=h("health_percent", _porcentaje),
        mana=h("mana"), mana_maximo=h("max_mana"), mana_porcentaje=h("mana_percent", _porcentaje),
        experiencia=h("xp"), reaparicion=h("respawn_seconds"), recompra_coste=h("buyback_cost"),
        recompra_recarga=h("buyback_cooldown"), ultimos_golpes=j("last_hits"), denegaciones=j("denies"),
        gpm=j("gpm"), xpm=j("xpm"), x=h("xpos", _numero), y=h("ypos", _numero),
        pausa=m("paused", _booleano), dia=m("daytime", _booleano), radiant=m("radiant_score"),
        dire=m("dire_score"), equipo=j("team_name", _texto),
    )
    estados = tuple((k, h(k, _booleano)) for k in ("silenced", "stunned", "disarmed", "magicimmune", "hexed", "muted", "break", "smoked", "has_debuff"))
    objetos = _bloque(payload, "items")
    habilidades = _bloque(payload, "abilities")
    inventario = []
    for clave, dato in sorted(objetos.items()):
        if not clave.startswith(("slot", "stash", "teleport", "neutral", "preserved_neutral")) or not isinstance(dato, dict):
            continue
        def o(k, convertir=_natural):
            return leer(dato, "items." + clave, k, convertir)
        inventario.append(Objeto(clave, o("name", _texto), o("can_cast", _booleano), o("passive", _booleano),
                                 o("item_level"), o("cooldown"), o("max_cooldown"), o("charges"), o("item_charges")))
    detalle = []
    for clave, dato in sorted(habilidades.items()):
        if not clave.startswith("ability") or not isinstance(dato, dict):
            continue
        def a(k, convertir=_natural):
            return leer(dato, "abilities." + clave, k, convertir)
        detalle.append(Habilidad(clave, a("name", _texto), a("level"), a("can_cast", _booleano),
                                a("ability_active", _booleano), a("passive", _booleano), a("ultimate", _booleano),
                                a("cooldown"), a("max_cooldown"), a("charges"), a("max_charges"), a("charge_cooldown")))
    return EstadoPartida(
        en_partida=bool(nombre) and nivel > 0, fase=fase, reloj=reloj if reloj is not None else 0,
        match_id=match_id, heroe=nombre, nivel=nivel, vivo=True if vivo is None else vivo,
        oro=oro or 0, kills=kills or 0, deaths=deaths or 0, assists=assists or 0, racha=racha or 0,
        items=_nombres_items(objetos), habilidades=_habilidades(habilidades),
        conocidos=frozenset(conocidos), invalidos=frozenset(invalidos), estados=estados,
        inventario=tuple(inventario), detalle_habilidades=tuple(detalle), **campos,
    )
