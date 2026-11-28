import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
from coach.draft.whisper_enigma import AudioWhisper, argumentos, escribir_wav

class WhisperTest(unittest.TestCase):
    def test_wav(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.wav'; escribir_wav(p,b'\x00\x04'*16000)
            with wave.open(str(p)) as f:
                self.assertEqual((f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes()),(1,2,16000,16000))
    def test_silencio(self):
        with self.assertRaisesRegex(RuntimeError,'silencioso'): escribir_wav('unused.wav',b'\0\0'*100)
    def test_argumentos(self):
        a=argumentos('C:/ruta con espacios/whisper-cli.exe','m.bin','a.wav','texto')
        self.assertEqual(a[0],'C:/ruta con espacios/whisper-cli.exe'); self.assertIn('-ng',a); self.assertIn('es',a)
    def test_cancelado(self):
        a=AudioWhisper('x','y'); t=a.ticket(); a.cancelar()
        with self.assertRaisesRegex(RuntimeError,'cancelado'): a.escuchar(t)
    def test_archivos_faltantes(self):
        a=AudioWhisper('no-existe.exe','no-existe.bin')
        with self.assertRaisesRegex(RuntimeError,'Selecciona'): a.escuchar(a.ticket())
    def test_transcripcion_simulada(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'whisper-cli.exe'; exe.touch(); modelo=Path(d)/'m.bin'; modelo.touch()
            a=AudioWhisper(exe,modelo)
            def proceso(args,**kw):
                Path(args[args.index('-of')+1]+'.txt').write_text('Soy mid',encoding='utf8')
                from unittest.mock import Mock
                p=Mock(); p.returncode=0; return p
            with patch.object(a,'capturar',return_value=b'\x00\x04'*16000),patch('coach.draft.whisper_enigma.subprocess.Popen',side_effect=proceso):
                self.assertEqual(a.escuchar(a.ticket()),'Soy mid')
