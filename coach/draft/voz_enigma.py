"""Audio local opcional, exclusivamente para el estudio offline."""
import base64
import os
import re
import subprocess
import threading
from pathlib import Path

PERSONALIDADES = ('Profesional', 'Asistente elegante', 'Peón orco', 'Grunt', 'Soldado raso', 'Mentor')


def limpiar(texto):
    texto = re.sub(r'[*#`_~]', '', texto)
    texto = re.sub(r'https?://\S+', '', texto)
    return ' '.join(''.join(c if c.isalnum() or c in ' .,;:?!¿¡%+-/\n' else ' ' for c in texto).split())[:4000]


def respuesta_contextual(respuesta, estado, personalidad='Profesional', sarcasmo=False):
    if personalidad not in PERSONALIDADES:
        raise ValueError('Personalidad desconocida')
    if respuesta.startswith('Indica candidatos disponibles'):
        respuesta = 'Contexto registrado. '+estado+' Puedes pedirme una comparación cuando quieras.'
    prefijos = {'Profesional':'', 'Asistente elegante':'Entendido. ', 'Peón orco':'Listo, jefe. ', 'Grunt':'A la orden. ', 'Soldado raso':'Recibido, comandante. ', 'Mentor':'Veamos. '}
    prefijo = prefijos[personalidad]
    if sarcasmo and 'No se emite una recomendación competitiva.' in respuesta and 'Información insuficiente' in respuesta:
        prefijo += 'La bola de cristal está de vacaciones. '
    return prefijo + respuesta


RECONOCER = r'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$r = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object {$_.Culture.TwoLetterISOLanguageName -eq 'es'} | Select-Object -First 1
if ($null -eq $r) { [Console]::WriteLine('NO_ES'); exit 0 }
$e = New-Object System.Speech.Recognition.SpeechRecognitionEngine -ArgumentList $r.Id
try {
 $e.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
 $e.SetInputToDefaultAudioDevice()
 $e.EndSilenceTimeout = [TimeSpan]::FromMilliseconds(700)
 $e.BabbleTimeout = [TimeSpan]::FromSeconds(5)
 $x = $e.Recognize([TimeSpan]::FromSeconds(5))
 if ($null -eq $x) { [Console]::WriteLine('SILENCIO') }
 elseif ($x.Confidence -lt 0.4) { [Console]::WriteLine('BAJA') }
 else { [Console]::WriteLine('OK:'+ [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($x.Text))) }
} finally { $e.Dispose() }
'''
HABLAR = r'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$t = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String([Console]::ReadLine()))
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
 $v = $s.GetInstalledVoices() | Where-Object {$_.Enabled -and $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq 'es'} | Select-Object -First 1
 if ($null -eq $v) { [Console]::WriteLine('NO_ES'); exit 0 }
 $s.SelectVoice($v.VoiceInfo.Name)
 $s.Speak($t)
 [Console]::WriteLine('OK')
} finally { $s.Dispose() }
'''


def interpretar_audio(salida):
    salida = salida.strip()
    if salida.startswith('OK:'):
        try:
            texto = base64.b64decode(salida[3:], validate=True).decode('utf-8').strip()
        except (ValueError, UnicodeError):
            raise RuntimeError('Respuesta de audio inválida') from None
        if texto and len(texto)<=1000:
            return texto
    raise RuntimeError({'NO_ES':'No hay reconocedor de español disponible en System.Speech.', 'SILENCIO':'No se reconoció voz.', 'BAJA':'Reconocimiento de baja confianza. Intenta de nuevo.'}.get(salida,'Respuesta de audio inválida'))


class AudioWindows:
    def __init__(self):
        self._lock = threading.Lock()
        self._proceso = None
        self._generacion = 0

    def cancelar(self):
        with self._lock:
            self._generacion += 1
            if self._proceso and self._proceso.poll() is None:
                self._proceso.kill()

    def ticket(self):
        with self._lock:
            return self._generacion

    def _ejecutar(self, codigo, datos, timeout, ticket):
        if os.name != 'nt':
            raise RuntimeError('Audio local disponible únicamente en Windows')
        exe = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        with self._lock:
            if ticket != self._generacion:
                raise RuntimeError('Audio cancelado')
            if self._proceso is not None:
                raise RuntimeError('Audio ocupado')
            p = subprocess.Popen([str(exe), '-NoProfile', '-NonInteractive', '-Command', codigo], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            self._proceso = p
        try:
            try:
                out, _ = p.communicate(datos, timeout=timeout)
            except subprocess.TimeoutExpired:
                p.kill(); p.communicate()
                raise RuntimeError('Tiempo de audio agotado') from None
            with self._lock:
                if ticket != self._generacion:
                    raise RuntimeError('Audio cancelado')
            if p.returncode:
                raise RuntimeError('Windows no pudo iniciar el audio. Revisa permisos y dispositivos.')
            return out.decode('ascii', errors='replace').strip()
        finally:
            with self._lock:
                self._proceso = None

    def escuchar(self, ticket):
        return interpretar_audio(self._ejecutar(RECONOCER, b'', 18, ticket))

    def hablar(self, texto, ticket):
        texto = limpiar(texto)
        if not texto: return
        r = self._ejecutar(HABLAR, base64.b64encode(texto.encode('utf-8'))+b'\n', 120, ticket)
        if r != 'OK':
            raise RuntimeError('No hay voz de español disponible en System.Speech.' if r=='NO_ES' else 'No se pudo reproducir la respuesta.')
