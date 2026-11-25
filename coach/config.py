"""Configuracion del usuario, guardada en su carpeta personal."""
import json
import os
import logging

log = logging.getLogger("coach.config")

CARPETA = os.path.join(os.path.expanduser("~"), ".dotacoach")
RUTA = os.path.join(CARPETA, "config.json")

DEFECTOS = {
    "proveedor": "gemini",
    "api_key": "",
    "modelo": "gemini-3.5-flash-lite",
    "persona": "profesional",
    "voz": True,
    "volumen": 0.9,
    "modo_competitivo": False,
    "puerto": 4125,
    "cooldown_ia": 25,
    "max_palabras": 22,
}


def cargar():
    cfg = dict(DEFECTOS)
    if os.path.exists(RUTA):
        try:
            with open(RUTA, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (OSError, ValueError) as error:
            log.warning("No se pudo leer la configuracion: %s", error)
    return cfg


def guardar(cfg):
    os.makedirs(CARPETA, exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
