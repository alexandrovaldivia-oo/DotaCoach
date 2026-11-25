"""Une todo: estado -> eventos y reglas -> consejos -> IA/voz/pantalla."""
import logging
import threading
import time
from collections import deque

from .eventos import detectar
from .persona import construir_prompt, persona
from .reglas import consejos_por_evento, consejos_por_tiempo
from .state import EstadoPartida, parsear
from .texto import limpiar_texto

log = logging.getLogger("coach.motor")


class Motor:
    def __init__(self, cfg, proveedor, voz, ui):
        self.cfg = cfg
        self.proveedor = proveedor
        self.voz = voz
        self.ui = ui
        self.estado = EstadoPartida()
        self._lock = threading.Lock()
        self._ia_ocupada = False
        self._ultima_ia = 0.0
        self._ultimo_aviso = 0.0
        self._memoria = deque(maxlen=8)
        self._avisado_sin_key = False
        self.aplicar_config()

    def aplicar_config(self):
        voz, tono, velocidad = persona(self.cfg.get("persona"))["voz"]
        self.voz.configurar(voz, tono, velocidad, self.cfg.get("volumen", 0.9))

    # Punto de entrada: cada mensaje de GSI llega aqui.
    def procesar(self, payload):
        act = parsear(payload)
        with self._lock:
            prev, self.estado = self.estado, act

        if act.en_partida:
            self.ui.estado("En partida: %s, minuto %d" % (act.heroe.replace("_", " "), act.minuto))
        else:
            self.ui.estado("Esperando partida de Dota 2...")

        if self.cfg.get("modo_competitivo") or not act.en_partida:
            return

        reloj_ref = prev.reloj if prev.en_partida else act.reloj
        consejos = consejos_por_tiempo(reloj_ref, act.reloj)
        for evento in detectar(prev, act):
            consejos += consejos_por_evento(evento, act)

        for consejo in sorted(consejos, key=lambda c: -c.prioridad):
            if consejo.usa_ia:
                self._pedir_ia(consejo, act)
            else:
                self._emitir(consejo.texto, consejo.prioridad)

    def _emitir(self, texto, prioridad=1):
        ahora = time.time()
        if prioridad < 2 and ahora - self._ultimo_aviso < 4:
            return
        self._ultimo_aviso = ahora
        texto = limpiar_texto(texto)
        self.ui.mostrar(texto)
        if self.cfg.get("voz", True):
            self.voz.hablar(texto)

    def _pedir_ia(self, consejo, estado):
        if not self.proveedor.disponible():
            if not self._avisado_sin_key:
                self._avisado_sin_key = True
                self.ui.mostrar("Falta la API key para los comentarios con IA.")
            return
        ahora = time.time()
        if self._ia_ocupada or ahora - self._ultima_ia < self.cfg.get("cooldown_ia", 25):
            return
        self._ia_ocupada = True
        self._ultima_ia = ahora

        def _trabajo():
            try:
                prompt = construir_prompt(self.cfg.get("persona"), estado, consejo.contexto,
                                          list(self._memoria), self.cfg.get("max_palabras", 22))
                texto = self.proveedor.generar(prompt)
                if texto:
                    texto = limpiar_texto(texto)
                    self._memoria.append(texto)
                    self._emitir(texto, consejo.prioridad)
            except Exception:
                log.exception("Fallo al pedir un consejo a la IA")
            finally:
                self._ia_ocupada = False

        threading.Thread(target=_trabajo, daemon=True).start()

    def probar_voz(self):
        self._emitir("Voz de prueba. Listo para entrenar.", 2)
