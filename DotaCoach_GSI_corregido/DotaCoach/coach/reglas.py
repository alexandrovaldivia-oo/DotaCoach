"""Motor de reglas DETERMINISTA. Lo que es logica pura no se le pregunta a la IA."""
from __future__ import annotations

from dataclasses import dataclass

from .datos import constantes as K
from .datos.nombres import nombre_legible


@dataclass(frozen=True)
class Consejo:
    texto: str = ""
    prioridad: int = 1          # 0 baja, 1 normal, 2 alta
    usa_ia: bool = False
    contexto: str = ""          # situacion que se le explica a la IA


def _cruzo(prev, act, momento):
    return prev < momento <= act


def consejos_por_tiempo(reloj_prev, reloj_act):
    consejos = []
    if reloj_act <= reloj_prev:
        return consejos

    for ciclo in range(1, K.SABIDURIA_MAXIMO_CICLOS + 1):
        aparicion = ciclo * K.SABIDURIA_INTERVALO
        if _cruzo(reloj_prev, reloj_act, aparicion - K.SABIDURIA_AVISO_ANTES):
            consejos.append(Consejo(
                "En %d segundos sale la runa de sabiduría." % K.SABIDURIA_AVISO_ANTES, 1))

    if _cruzo(reloj_prev, reloj_act, K.TORMENTOR_APARICION - K.TORMENTOR_AVISO_ANTES):
        consejos.append(Consejo("Se acerca la aparición de Tormentor. Revisa si tu equipo puede tomarlo.", 1))
    return consejos


def consejos_por_evento(evento, estado):
    if evento.tipo == "inicio":
        return [Consejo("Partida detectada con %s." % estado.heroe.replace("_", " "), 1)]

    if evento.tipo == "nivel" and evento.valor in K.NIVELES_DEFINITIVA:
        return [Consejo("Nivel %d. Ya puedes mejorar tu definitiva." % evento.valor, 1)]

    if evento.tipo == "muerte":
        return [Consejo(usa_ia=True, prioridad=1,
                        contexto="Acabo de morir. Dame un consejo corto para no repetirlo.")]

    if evento.tipo == "racha":
        return [Consejo(usa_ia=True, prioridad=1,
                        contexto="Llevo una racha de %d bajas seguidas. Reacciona con un comentario corto." % evento.valor)]

    if evento.tipo == "item_nuevo":
        return [Consejo(usa_ia=True, prioridad=0,
                        contexto="Acabo de comprar %s. Evalúa en una frase si tiene sentido en esta fase." % nombre_legible(evento.dato))]

    return []
