"""Servidor Whisper experimental, únicamente loopback y bajo demanda."""
import atexit
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from coach.draft.whisper_enigma import AudioWhisper, PROMPT, escribir_wav


def argumentos_servidor(exe, modelo, puerto, prefijo, gpu):
    return [str(exe), '-m', str(modelo), '-l', 'es', '--prompt', PROMPT,
            '--host', '127.0.0.1', '--port', str(puerto), '--request-path', prefijo,
            '--public', str(Path(exe).parent / '__enigma_sin_web__')] + ([] if gpu else ['-ng'])


def texto_respuesta(datos):
    texto = datos.get('text') if isinstance(datos, dict) else None
    if not isinstance(texto, str) or not texto.strip() or len(texto.strip()) > 1000:
        raise RuntimeError('Respuesta de Whisper residente inválida.')
    return texto.strip()


class AudioWhisperResidente(AudioWhisper):
    def __init__(self, exe, modelo, **kw):
        super().__init__(exe, modelo, **kw)
        self._servidor = None
        self._gpu_servidor = None
        self._url = None
        atexit.register(self.cerrar)

    def cerrar(self):
        with self._lock:
            p, self._servidor = self._servidor, None
            self._url = None
            if p is not None and p.poll() is None:
                p.kill()
                p.wait(timeout=5)

    def cancelar(self):
        super().cancelar()
        self.cerrar()

    def iniciar(self, ticket, sesion):
        self.comprobar(ticket)
        if self._servidor is not None and self._servidor.poll() is None and self._gpu_servidor == self.gpu:
            return 0
        self.cerrar()
        inicio = time.perf_counter()
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            puerto = s.getsockname()[1]
        prefijo = '/enigma-' + uuid.uuid4().hex
        url = f'http://127.0.0.1:{puerto}{prefijo}'
        with self._lock:
            if ticket != self._generacion:
                raise RuntimeError('Audio cancelado')
            try:
                p = subprocess.Popen(argumentos_servidor(self.exe, self.modelo, puerto, prefijo, self.gpu),
                    cwd=str(self.exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            except OSError:
                raise RuntimeError('No se pudo iniciar whisper-server. Revisa DLL y protección de Windows.') from None
            self._servidor, self._url, self._gpu_servidor = p, url, self.gpu
        try:
            import requests
            while time.perf_counter() - inicio < 45:
                self.comprobar(ticket)
                if p.poll() is not None:
                    raise RuntimeError('Whisper servidor terminó antes de estar listo.')
                try:
                    r = sesion.get(url + '/health', timeout=0.5, allow_redirects=False)
                    if r.status_code == 200 and r.json().get('status') == 'ok':
                        self.comprobar(ticket)
                        return round((time.perf_counter()-inicio)*1000)
                except (requests.RequestException, ValueError, AttributeError):
                    pass
                time.sleep(0.1)
            raise RuntimeError('Whisper servidor no estuvo listo en 45 segundos.')
        except BaseException:
            self.cerrar()
            raise

    def escuchar(self, ticket):
        import requests
        self.comprobar(ticket)
        if not self.exe.is_file() or not self.modelo.is_file():
            raise RuntimeError('Selecciona whisper-server.exe y el modelo multilingüe.')
        self.metricas = {}
        with requests.Session() as sesion:
            sesion.trust_env = False
            self.progreso('Preparando modelo residente', 0)
            self.metricas['carga_ms'] = self.iniciar(ticket, sesion)
            try:
                self.progreso('Esperando voz', 0)
                inicio = time.perf_counter()
                pcm = self.capturar(ticket)
                self.metricas['captura_ms'] = round((time.perf_counter()-inicio)*1000)
                with tempfile.TemporaryDirectory(prefix='enigma_audio_') as carpeta:
                    wav = Path(carpeta)/'voz.wav'
                    escribir_wav(wav, pcm)
                    self.comprobar(ticket)
                    url = self._url
                    if url is None:
                        raise RuntimeError('Audio cancelado')
                    self.progreso('Transcribiendo', 0)
                    inicio = time.perf_counter()
                    with wav.open('rb') as f:
                        r = sesion.post(url+'/inference', files={'file': ('voz.wav', f, 'audio/wav')},
                            data={'response_format':'json'}, timeout=(2, 60), allow_redirects=False)
                    self.comprobar(ticket)
                    if r.status_code != 200:
                        raise RuntimeError(f'Whisper residente: HTTP {r.status_code}.')
                    texto = texto_respuesta(r.json())
                    self.metricas['transcripcion_ms'] = round((time.perf_counter()-inicio)*1000)
                    return texto
            except (requests.RequestException, ValueError):
                self.cerrar()
                self.comprobar(ticket)
                raise RuntimeError('Falló la comunicación local con Whisper residente.') from None
