"""Limpieza de texto: todo lo que se muestra o se habla pasa por aqui."""
import re

_EMOJIS = re.compile("[\U00010000-\U0010ffff\u2600-\u27bf]")
_SIMBOLOS = re.compile(r"[*#`~^|<>]")


def limpiar_texto(texto):
    if not texto:
        return ""
    limpio = _EMOJIS.sub("", str(texto))
    limpio = _SIMBOLOS.sub("", limpio)
    limpio = limpio.replace("_", " ")
    return re.sub(r"\s+", " ", limpio).strip()
