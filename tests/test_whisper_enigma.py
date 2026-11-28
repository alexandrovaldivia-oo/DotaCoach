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

class SegmentacionTest(unittest.TestCase):
    def test_fin_por_silencio(self):
        from coach.draft.whisper_enigma import CapturaFrase
        f=CapturaFrase(); silencio=b'\0\0'*1600; voz=b'\x00\x04'*1600
        for b in [silencio]*3+[voz]*4+[silencio]*5: f.agregar(b)
        self.assertTrue(f.fin); self.assertTrue(f.iniciada); self.assertIn(voz,f.resultado()); self.assertLess(len(f.resultado()),6*32000)
    def test_espera_sin_voz(self):
        from coach.draft.whisper_enigma import CapturaFrase
        f=CapturaFrase(espera=3)
        for _ in range(3): f.agregar(b'\0\0'*1600)
        self.assertTrue(f.fin)
        with self.assertRaisesRegex(RuntimeError,'No se detectó voz'): f.resultado()
    def test_ruido_breve_no_activa(self):
        from coach.draft.whisper_enigma import CapturaFrase
        f=CapturaFrase(); f.agregar(b'\x00\x04'*1600); f.agregar(b'\0\0'*1600)
        self.assertFalse(f.iniciada)
    def test_limite_frase(self):
        from coach.draft.whisper_enigma import CapturaFrase
        f=CapturaFrase(max_bloques=4)
        for _ in range(4): f.agregar(b'\x00\x04'*1600)
        self.assertTrue(f.fin)
    def test_gpu_opcional(self):
        self.assertNotIn('-ng',argumentos('x','m','w','s',gpu=True))
