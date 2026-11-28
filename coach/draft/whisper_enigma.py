"""Captura local y transcripción con whisper.cpp. Sin red ni acceso al juego."""
import array
import math
import os
from pathlib import Path
import subprocess
import tempfile
import wave
import time
from collections import deque

from coach.draft.voz_enigma import AudioWindows

PROMPT = 'Conversación en español sobre Dota 2. ENIGMA, mid, offlane, carry, Lion, Axe, Puck, Queen of Pain, Rubick, Spirit Breaker, BKB.'


def nivel(pcm):
    muestras = array.array('h', pcm)
    return math.sqrt(sum(x*x for x in muestras)/len(muestras)) if muestras else 0


class CapturaFrase:
    """Segmentación heurística por energía, no VAD neuronal. Bloques de 100 ms."""
    def __init__(self, umbral=80, espera=80, max_bloques=150, silencio=5):
        self.umbral=umbral; self.espera=espera; self.max_bloques=max_bloques; self.silencio=silencio
        self.previos=deque(maxlen=4); self.bloques=[]; self.total=0; self.pausa=0; self.voz=0
        self.iniciada=False; self.fin=False; self.pico=0

    def agregar(self, pcm):
        if self.fin: raise RuntimeError('Captura terminada')
        self.total+=1; rms=nivel(pcm); self.pico=max(self.pico,rms)
        activo=rms>=self.umbral
        if not self.iniciada:
            self.previos.append(pcm)
            self.voz=self.voz+1 if activo else 0
            if self.voz>=2:
                self.iniciada=True; self.bloques.extend(self.previos)
            elif self.total>=self.espera:
                self.fin=True
        else:
            self.bloques.append(pcm); self.pausa=0 if activo else self.pausa+1
            self.fin=self.pausa>=self.silencio or len(self.bloques)>=self.max_bloques
        return self.fin

    def resultado(self):
        if not self.iniciada: raise RuntimeError(f'No se detectó voz. Pico RMS: {self.pico:.0f}; umbral: {self.umbral}. Revisa entrada o sensibilidad.')
        return b''.join(self.bloques)


def dispositivos():
    try:
        import sounddevice as sd
        return [(i,d['name']) for i,d in enumerate(sd.query_devices()) if d['max_input_channels']>0]
    except Exception:
        raise RuntimeError('No se pudieron enumerar los micrófonos.') from None


def escribir_wav(ruta, pcm):
    if not pcm or len(pcm) % 2:
        raise RuntimeError('Captura de audio inválida.')
    if nivel(pcm) < 15:
        raise RuntimeError('Audio casi silencioso. Revisa el micrófono seleccionado.')
    with wave.open(str(ruta), 'wb') as f:
        f.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        f.writeframes(pcm)


def argumentos(exe, modelo, wav, salida, gpu=False):
    return [str(exe), '-m', str(modelo), '-f', str(wav), '-l', 'es',
            '--prompt', PROMPT, '-otxt', '-of', str(salida)] + ([] if gpu else ['-ng'])


class AudioWhisper(AudioWindows):
    def __init__(self, exe, modelo, dispositivo=None, umbral=80, gpu=False, progreso=None):
        super().__init__()
        self.exe = Path(exe).resolve()
        self.modelo = Path(modelo).resolve()
        self.dispositivo=dispositivo; self.umbral=umbral; self.gpu=gpu; self.progreso=progreso or (lambda *a: None)
        self.metricas={}

    def comprobar(self, ticket):
        if ticket != self.ticket():
            raise RuntimeError('Audio cancelado')

    def capturar(self, ticket):
        try:
            import sounddevice as sd
        except (ImportError, OSError):
            raise RuntimeError('Captura de micrófono no disponible en esta compilación.') from None
        frase=CapturaFrase(umbral=self.umbral)
        try:
            with sd.RawInputStream(device=self.dispositivo, samplerate=16000, channels=1, dtype='int16', blocksize=1600) as stream:
                while not frase.fin:
                    self.comprobar(ticket)
                    datos, overflow = stream.read(1600)
                    if overflow:
                        raise RuntimeError('Se perdieron muestras del micrófono. Intenta otra vez.')
                    pcm=bytes(datos); frase.agregar(pcm)
                    self.progreso('Hablando' if frase.iniciada else 'Esperando voz', nivel(pcm))
        except sd.PortAudioError:
            raise RuntimeError('No se pudo capturar a 16 kHz. Revisa permisos y dispositivo seleccionado.') from None
        self.comprobar(ticket)
        return frase.resultado()

    def escuchar(self, ticket):
        self.comprobar(ticket)
        if not self.exe.is_file() or not self.modelo.is_file():
            raise RuntimeError('Selecciona whisper-cli.exe y el modelo multilingüe .bin.')
        with tempfile.TemporaryDirectory(prefix='enigma_audio_') as carpeta:
            wav = Path(carpeta)/'voz.wav'
            salida = Path(carpeta)/'texto'
            self.metricas={}
            inicio=time.perf_counter()
            pcm=self.capturar(ticket)
            self.metricas["captura_ms"]=round((time.perf_counter()-inicio)*1000)
            escribir_wav(wav, pcm)
            self.progreso("Transcribiendo", 0)
            inicio=time.perf_counter()
            with self._lock:
                if ticket != self._generacion:
                    raise RuntimeError('Audio cancelado')
                if self._proceso is not None:
                    raise RuntimeError('Audio ocupado')
                try:
                    p = subprocess.Popen(argumentos(self.exe,self.modelo,wav,salida,self.gpu), cwd=str(self.exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
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
                self.metricas["transcripcion_ms"]=round((time.perf_counter()-inicio)*1000)
                return texto
            finally:
                with self._lock:
                    self._proceso = None
