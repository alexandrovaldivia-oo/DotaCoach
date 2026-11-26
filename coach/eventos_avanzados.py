"""Detector experimental puro, sin efectos de voz, IA ni red."""
from collections import Counter
from .eventos import Evento


def _inventario(e):
    # Solo inventario, mochila y alijo: excluye teleport y neutrales.
    return {o.casilla: o.nombre for o in e.inventario
            if o.casilla.startswith(('slot', 'stash'))}


def detectar_avanzados(prev, act):
    eventos = []
    if prev.match_id and act.match_id and prev.match_id != act.match_id:
        return [Evento('partida_nueva')]
    if prev.fase and act.fase and prev.fase != act.fase:
        eventos.append(Evento('fase', act.fase))
    if prev.pausa is not None and act.pausa is not None and prev.pausa != act.pausa:
        eventos.append(Evento('pausa' if act.pausa else 'reanudacion'))
    if not (prev.fase_activa and act.fase_activa and prev.en_partida and act.en_partida
            and prev.heroe == act.heroe and prev.match_id and prev.match_id == act.match_id
            and prev.pausa is False and act.pausa is False):
        return eventos
    def conocido(k):
        return k in prev.conocidos and k in act.conocidos
    if conocido('map.clock_time') and act.reloj < prev.reloj:
        return eventos
    if conocido('hero.level') and act.nivel > prev.nivel:
        eventos.append(Evento('nivel', valor=act.nivel))
    vida_conocida = conocido('hero.alive')
    delta = act.deaths - prev.deaths if conocido('player.deaths') else 0
    if delta > 0 or (vida_conocida and prev.vivo and not act.vivo):
        eventos.append(Evento('muerte', valor=max(1, delta)))
    if vida_conocida and not prev.vivo and act.vivo:
        eventos.append(Evento('reaparicion'))
    if vida_conocida and prev.vivo and act.vivo:
        for nombre, anterior, actual, umbral in (
            ('vida', prev.vida_porcentaje, act.vida_porcentaje, 25),
            ('mana', prev.mana_porcentaje, act.mana_porcentaje, 20),
        ):
            if anterior is None or actual is None:
                continue
            if anterior > umbral >= actual:
                eventos.append(Evento(nombre + '_baja', valor=actual))
            elif anterior <= umbral < actual:
                eventos.append(Evento(nombre + '_recuperada', valor=actual))
        anteriores = {a.nombre: a for a in prev.detalle_habilidades if a.nombre and a.definitiva is True}
        for a in act.detalle_habilidades:
            p = anteriores.get(a.nombre)
            if (p and a.definitiva is True and a.pasiva is False and p.pasiva is False
                and p.nivel and a.nivel and p.recarga is not None and p.recarga > 0
                and a.recarga == 0 and a.disponible is True):
                eventos.append(Evento('definitiva_disponible', a.nombre))
    if conocido('player.kills') and act.kills > prev.kills:
        eventos.append(Evento('kill', valor=act.kills-prev.kills))
    if conocido('player.kill_streak') and act.racha > prev.racha:
        hit = [u for u in (3, 5, 7, 10) if prev.racha < u <= act.racha]
        if hit:
            eventos.append(Evento('racha', valor=max(hit)))
    antes, ahora = _inventario(prev), _inventario(act)
    # Comparar solo snapshots completos y con mismas casillas; no inferir ausencia.
    requeridas = {'slot%d' % i for i in range(9)} | {'stash%d' % i for i in range(6)}
    if antes.keys() == ahora.keys() and requeridas <= antes.keys() and all(antes.values()) and all(ahora.values()):
        ca = Counter(n for n in antes.values() if n != 'empty')
        cb = Counter(n for n in ahora.values() if n != 'empty')
        for n, cantidad in sorted((cb-ca).items()):
            eventos.append(Evento('item_incorporado', n, cantidad))
        for n, cantidad in sorted((ca-cb).items()):
            eventos.append(Evento('item_retirado', n, cantidad))
        for n in sorted(ca.keys() & cb.keys()):
            if ca[n] == cb[n] and {k for k,v in antes.items() if v==n} != {k for k,v in ahora.items() if v==n}:
                eventos.append(Evento('item_movido', n))
    return eventos
