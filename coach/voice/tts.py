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

    def hablar(self, texto):
        texto = limpiar_texto(texto)
        if not texto:
            return
        try:
            self._cola.put_nowait(texto)
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

    def _trabajar(self):
        while True:
            texto = self._cola.get()
            ruta = os.path.join(tempfile.gettempdir(), "dotacoach_%d.mp3" % int(time.time() * 1000))
            try:
                self._sintetizar(texto, ruta)
                mixer = self._iniciar_mixer()
                mixer.music.set_volume(self.volumen)
                mixer.music.load(ruta)
                mixer.music.play()
                while mixer.music.get_busy():
                    time.sleep(0.1)
                mixer.music.unload()
            except Exception:
                log.exception("No se pudo reproducir la voz")
            finally:
                try:
                    os.remove(ruta)
                except OSError:
                    pass
