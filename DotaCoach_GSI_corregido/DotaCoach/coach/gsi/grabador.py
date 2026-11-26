"""Guarda el JSON crudo de GSI y la lista de campos recibidos (modo diagnostico)."""
import json
import os
import time
import threading


class GrabadorGSI:
    def __init__(self, carpeta=None):
        carpeta = carpeta or os.path.join(os.path.expanduser("~"), "gsi_logs")
        os.makedirs(carpeta, exist_ok=True)
        sello = time.strftime("%Y%m%d_%H%M%S")
        self.ruta_log = os.path.join(carpeta, "partida_%s.jsonl" % sello)
        self.ruta_campos = os.path.join(carpeta, "campos_vistos_%s.txt" % sello)
        self._lock = threading.RLock()
        self.campos = set()
        self.mensajes = 0
        self._ultimo_resumen = 0.0

    def _recopilar(self, obj, prefijo):
        if isinstance(obj, dict):
            for clave, valor in obj.items():
                ruta = prefijo + "." + clave if prefijo else clave
                self.campos.add(ruta)
                self._recopilar(valor, ruta)

    def __call__(self, datos):
        with self._lock:
            self._registrar(datos)

    def _registrar(self, datos):
        with open(self.ruta_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "datos": datos}, ensure_ascii=False) + "\n")
        self._recopilar(datos, "")
        self.mensajes += 1
        ahora = time.time()
        if ahora - self._ultimo_resumen >= 10:
            self._ultimo_resumen = ahora
            self.cerrar()
            mapa = datos.get("map", {}) if isinstance(datos.get("map"), dict) else {}
            hero = datos.get("hero", {}) if isinstance(datos.get("hero"), dict) else {}
            print("[%d mensajes] reloj=%s heroe=%s nivel=%s" % (
                self.mensajes, mapa.get("clock_time", "?"),
                str(hero.get("name", "?")).replace("npc_dota_hero_", ""), hero.get("level", "?")))

    def cerrar(self):
        with self._lock:
            temporal = self.ruta_campos + ".tmp"
            with open(temporal, "w", encoding="utf-8") as f:
                for ruta in sorted(self.campos):
                    f.write(ruta + "\n")
            os.replace(temporal, self.ruta_campos)
        return self.ruta_campos
