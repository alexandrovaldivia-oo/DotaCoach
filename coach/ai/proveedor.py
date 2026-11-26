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
                  "generationConfig": {"temperature": 0.85, "maxOutputTokens": 512}}
        url = "https://%s/v1beta/models/%s:generateContent" % (_DOMINIO_GEMINI, self.cfg.get("modelo"))
        try:
            r = requests.post(url, json=cuerpo, timeout=10,
                              headers={"Content-Type": "application/json",
                                       "x-goog-api-key": self.cfg.get("api_key", "")})
        except requests.RequestException as error:
            log.warning("Fallo de red con Gemini: %s", type(error).__name__)
            return None
        if r.status_code != 200:
            log.warning("Gemini respondio %s", r.status_code)
            return None
        try:
            datos = r.json()
        except ValueError:
            log.warning("Gemini: JSON invalido")
            return None
        if not isinstance(datos, dict):
            log.warning("Gemini: estructura invalida")
            return None
        for candidato in datos.get("candidates") or []:
            motivo = candidato.get("finishReason")
            log.info("Gemini HTTP 200; finalizacion: %s", motivo if motivo in
                     {"STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"} else "NO_CLASIFICADA")
            if motivo != "STOP":
                continue
            textos = [parte["text"].strip() for parte in
                      (candidato.get("content") or {}).get("parts") or []
                      if parte.get("thought") is not True and isinstance(parte.get("text"), str)]
            texto = " ".join(t for t in textos if t)
            if texto:
                log.info("Gemini: texto final recibido; palabras=%d", len(texto.split()))
                return texto
        log.info("Gemini: sin texto final completo")
        return None


def crear_proveedor(cfg):
    if cfg.get("proveedor", "gemini") == "gemini":
        return ProveedorGemini(cfg)
    raise ValueError("Proveedor de IA no soportado todavia: %s" % cfg.get("proveedor"))
