"""Servidor local que recibe lo que Dota 2 envia por GSI."""
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .setup import HOST

log = logging.getLogger("coach.gsi.server")


class ServidorGSI:
    def __init__(self, puerto, callbacks):
        self._callbacks = list(callbacks)
        servidor = self

        class Manejador(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    largo = int(self.headers.get("Content-Length", 0))
                    datos = json.loads(self.rfile.read(largo).decode("utf-8"))
                except (ValueError, OSError) as error:
                    log.warning("Mensaje GSI ilegible: %s", error)
                    datos = None
                if datos is not None:
                    servidor._despachar(datos)
                self.send_response(200)
                self.end_headers()

            def log_message(self, formato, *args):
                return

        self.httpd = ThreadingHTTPServer((HOST, puerto), Manejador)
        self.puerto = self.httpd.server_address[1]

    def _despachar(self, datos):
        for callback in self._callbacks:
            try:
                callback(datos)
            except Exception:
                log.exception("Error en un procesador de GSI")

    def iniciar_en_hilo(self):
        hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        hilo.start()
        return hilo

    def servir(self):
        self.httpd.serve_forever()

    def detener(self):
        self.httpd.shutdown()
        self.httpd.server_close()
