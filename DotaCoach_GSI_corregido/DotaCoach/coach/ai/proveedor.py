"""Capa de IA intercambiable. El resto del programa solo conoce ProveedorIA.
Hoy: Gemini con tu propia key. Mas adelante: tu propio servidor, sin tocar el resto."""
from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod

import requests

log = logging.getLogger("coach.ai")

_DOMINIO_GEMINI = "generativelanguage" + ".googleapis.com"


class ProveedorIA(ABC):
    @abstractmethod
    def disponible(self):
        """True si hay lo necesario para responder (por ejemplo, una API key)."""

    @abstractmethod
    def generar(self, prompt, imagen_jpeg=None):
        """Devuelve el texto generado, o None si fallo."""


class ProveedorGemini(ProveedorIA):
    def __init__(self, cfg):
        self.cfg = cfg  # referencia viva: si cambia la key, se usa la nueva

    def disponible(self):
        return bool(self.cfg.get("api_key"))

    def generar(self, prompt, imagen_jpeg=None):
        if not self.disponible():
            return None
        partes = [{"text": prompt}]
        if imagen_jpeg:
            partes.append({"inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(imagen_jpeg).decode("ascii")}})
        cuerpo = {"contents": [{"parts": partes}],
                  "generationConfig": {"temperature": 0.85, "maxOutputTokens": 160}}
        url = "https://%s/v1beta/models/%s:generateContent" % (_DOMINIO_GEMINI, self.cfg.get("modelo"))
        try:
            r = requests.post(url, json=cuerpo, timeout=10,
                              headers={"Content-Type": "application/json",
                                       "x-goog-api-key": self.cfg.get("api_key", "")})
        except requests.RequestException as error:
            log.warning("Fallo de red con Gemini: %s", error)
            return None
        if r.status_code != 200:
            log.warning("Gemini respondio %s: %s", r.status_code, r.text[:200])
            return None
        try:
            datos = r.json()
        except ValueError:
            return None
        for candidato in datos.get("candidates") or []:
            for parte in (candidato.get("content") or {}).get("parts") or []:
                texto = parte.get("text")
                if texto:
                    return texto.strip()
        return None


def crear_proveedor(cfg):
    if cfg.get("proveedor", "gemini") == "gemini":
        return ProveedorGemini(cfg)
    raise ValueError("Proveedor de IA no soportado todavia: %s" % cfg.get("proveedor"))
