"""Voz del coach. Nivel 1: edge-tts (nube, sin instalar modelos).
Las voces clonadas locales se enchufaran despues como otro motor opcional."""
import asyncio
import logging
import os
import queue
import tempfile
import threading
import time

from ..texto import limpiar_texto

log = logging.getLogger("coach.voz")


class ReproductorVoz:
    def __init__(self, volumen=0.9):
        self.volumen = volumen
        self.voz = "es-MX-JorgeNeural"
        self.tono = "+0Hz"
        self.velocidad = "+0%"
        self._cola = queue.Queue(maxsize=3)
        self._mixer = None
        threading.Thread(target=self._trabajar, daemon=True).start()

    def configurar(self, voz, tono, velocidad, volumen=None):
        self.voz, self.tono, self.velocidad = voz, tono, velocidad
        if volumen is not None:
            self.volumen = volumen

    def hablar(self, texto, vigente=None):
        texto = limpiar_texto(texto)
        if not texto:
            return
        try:
            self._cola.put_nowait((texto, vigente))
        except queue.Full:
            log.info("Cola de voz llena: se descarta un mensaje")

    def _iniciar_mixer(self):
        if self._mixer is None:
            import pygame
            pygame.mixer.init()
            self._mixer = pygame.mixer
        return self._mixer

    def _sintetizar(self, texto, ruta):
        import edge_tts

        async def _generar():
            comunicador = edge_tts.Communicate(texto, self.voz, pitch=self.tono, rate=self.velocidad)
            await comunicador.save(ruta)

        asyncio.run(_generar())

    def _reproducir(self, texto, vigente):
        # Un nombre exclusivo evita colisiones incluso entre procesos.
        ruta = None
        musica = None
        cargado = False
        iniciado = False
        try:
            if vigente is not None and not vigente():
                log.info("Voz descartada antes de sintetizar")
                return
            with tempfile.NamedTemporaryFile(prefix="dotacoach_", suffix=".mp3", delete=False) as f:
                ruta = f.name
            self._sintetizar(texto, ruta)
            if vigente is not None and not vigente():
                log.info("Voz descartada despues de sintetizar")
                return
            musica = self._iniciar_mixer().music
            musica.set_volume(self.volumen)
            musica.load(ruta)
            cargado = True
            if vigente is not None and not vigente():
                log.info("Voz descartada antes de reproducir")
                return
            # La vigencia de entrega no limita la duración de un audio iniciado.
            durante = getattr(vigente, "durante", vigente)
            musica.play()
            iniciado = True
            log.info("Voz: reproduccion iniciada")
            while musica.get_busy():
                if durante is not None and not durante():
                    musica.stop()
                    iniciado = False
                    log.info("Voz: reproduccion interrumpida por control de continuidad")
                    break
                time.sleep(0.1)
            else:
                log.info("Voz: reproduccion finalizada")
                iniciado = False
        except Exception:
            # No imprimir contenido del consejo ni detalles de servicios externos.
            log.warning("No se pudo reproducir la voz")
        finally:
            if cargado:
                try:
                    if iniciado:
                        musica.stop()
                    musica.unload()
                except Exception:
                    log.warning("No se pudo liberar el audio")
            if ruta is not None:
                try:
                    os.remove(ruta)
                except OSError:
                    pass

    def _trabajar(self):
        while True:
            texto, vigente = self._cola.get()
            try:
                self._reproducir(texto, vigente)
            finally:
                self._cola.task_done()
