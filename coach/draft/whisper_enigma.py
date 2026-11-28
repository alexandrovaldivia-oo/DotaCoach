"""Captura local y transcripción con whisper.cpp. Sin red ni acceso al juego."""
import array
import math
import os
from pathlib import Path
import subprocess
import tempfile
import wave

from coach.draft.voz_enigma import AudioWindows

PROMPT = 'Conversación en español sobre Dota 2. ENIGMA, mid, offlane, carry, Lion, Axe, Puck, Queen of Pain, Rubick, Spirit Breaker, BKB.'


def escribir_wav(ruta, pcm):
    if not pcm or len(pcm) % 2:
        raise RuntimeError('Captura de audio inválida.')
    muestras = array.array('h', pcm)
    rms = math.sqrt(sum(x*x for x in muestras)/len(muestras))
    if rms < 35:
        raise RuntimeError('Audio casi silencioso. Revisa el micrófono predeterminado.')
    with wave.open(str(ruta), 'wb') as f:
        f.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        f.writeframes(pcm)


def argumentos(exe, modelo, wav, salida):
    return [str(exe), '-m', str(modelo), '-f', str(wav), '-l', 'es',
            '--prompt', PROMPT, '-otxt', '-of', str(salida), '-ng']


class AudioWhisper(AudioWindows):
    def __init__(self, exe, modelo):
        super().__init__()
        self.exe = Path(exe).resolve()
        self.modelo = Path(modelo).resolve()

    def comprobar(self, ticket):
        if ticket != self.ticket():
            raise RuntimeError('Audio cancelado')

    def capturar(self, ticket):
        try:
            import sounddevice as sd
        except (ImportError, OSError):
            raise RuntimeError('Captura de micrófono no disponible en esta compilación.') from None
        bloques = []
        try:
            with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1600) as stream:
                for _ in range(60):
                    self.comprobar(ticket)
                    datos, overflow = stream.read(1600)
                    if overflow:
                        raise RuntimeError('Se perdieron muestras del micrófono. Intenta otra vez.')
                    bloques.append(bytes(datos))
        except sd.PortAudioError:
            raise RuntimeError('No se pudo capturar a 16 kHz. Revisa permisos y dispositivo predeterminado.') from None
        return b''.join(bloques)

    def escuchar(self, ticket):
        self.comprobar(ticket)
        if not self.exe.is_file() or not self.modelo.is_file():
            raise RuntimeError('Selecciona whisper-cli.exe y el modelo multilingüe .bin.')
        with tempfile.TemporaryDirectory(prefix='enigma_audio_') as carpeta:
            wav = Path(carpeta)/'voz.wav'
            salida = Path(carpeta)/'texto'
            escribir_wav(wav, self.capturar(ticket))
            with self._lock:
                if ticket != self._generacion:
                    raise RuntimeError('Audio cancelado')
                if self._proceso is not None:
                    raise RuntimeError('Audio ocupado')
                try:
                    p = subprocess.Popen(argumentos(self.exe,self.modelo,wav,salida), cwd=str(self.exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                except OSError:
                    raise RuntimeError('No se pudo iniciar Whisper. Revisa sus DLL y las protecciones de Windows.') from None
                self._proceso = p
            try:
                try:
                    p.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    p.kill(); p.wait()
                    raise RuntimeError('Whisper superó el tiempo de espera.') from None
                self.comprobar(ticket)
                archivo = salida.with_suffix('.txt')
                if p.returncode != 0 or not archivo.is_file():
                    raise RuntimeError('Whisper no pudo transcribir. Revisa modelo y ejecutable.')
                texto = archivo.read_text(encoding='utf-8-sig').strip()
                if not texto or len(texto)>1000:
                    raise RuntimeError('Transcripción vacía o demasiado extensa.')
                return texto
            finally:
                with self._lock:
                    self._proceso = None
