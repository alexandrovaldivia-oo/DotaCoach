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
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from coach.draft.whisper_residente import AudioWhisperResidente, argumentos_servidor, texto_respuesta

class ResidenteTest(unittest.TestCase):
    def test_loopback(self):
        a=argumentos_servidor('x','m',1234,'/abc',False)
        self.assertEqual(a[a.index('--host')+1],'127.0.0.1')
        self.assertIn('-ng',a)
        self.assertNotIn('-ng',argumentos_servidor('x','m',1234,'/abc',True))
    def test_respuesta(self):
        self.assertEqual(texto_respuesta({'text':' Soy mid '}),'Soy mid')
        for bad in ({}, {'text':None},{'text':' '},{'text':'x'*1001}):
            with self.assertRaises(RuntimeError): texto_respuesta(bad)
    def test_reutilizacion(self):
        a=AudioWhisperResidente('x','m'); p=Mock(); p.poll.return_value=None
        a._servidor=p; a._gpu_servidor=False
        self.assertEqual(a.iniciar(a.ticket(),Mock()),0)
        a.cancelar(); p.kill.assert_called_once(); self.assertIsNone(a._servidor)
    def test_transcripcion(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'whisper-server.exe'; exe.touch(); modelo=Path(d)/'m.bin'; modelo.touch()
            a=AudioWhisperResidente(exe,modelo); a._url='http://127.0.0.1:1234/abc'
            s=Mock(); s.post.return_value.status_code=200; s.post.return_value.json.return_value={'text':'Lion y Axe'}
            with patch('requests.Session') as factory, patch.object(a,'iniciar',return_value=0), patch.object(a,'capturar',return_value=b'\x00\x04'*16000):
                factory.return_value.__enter__.return_value=s
                self.assertEqual(a.escuchar(a.ticket()),'Lion y Axe')
                self.assertFalse(s.trust_env)
                self.assertEqual(s.post.call_args.args[0],a._url+'/inference')
                self.assertFalse(s.post.call_args.kwargs['allow_redirects'])
    def test_inicio(self):
        a=AudioWhisperResidente('x','m'); p=Mock(); p.poll.return_value=None
        s=Mock(); s.get.return_value.status_code=200; s.get.return_value.json.return_value={'status':'ok'}
        with patch('coach.draft.whisper_residente.subprocess.Popen',return_value=p) as abrir:
            a.iniciar(a.ticket(),s); a.iniciar(a.ticket(),s)
            abrir.assert_called_once()
        a.cerrar()

class RapidoTest(unittest.TestCase):
    def test_perfil_optativo(self):
        normal=argumentos_servidor('x','m',1234,'/abc',True)
        rapido=argumentos_servidor('x','m',1234,'/abc',True,True)
        self.assertEqual(rapido[:len(normal)],normal)
        self.assertEqual(rapido[len(normal):],['--best-of','1','--beam-size','1','--no-fallback','--no-context'])
    def test_cambio_perfil_reinicia(self):
        a=AudioWhisperResidente('x','m'); anterior=Mock(); anterior.poll.return_value=None
        nuevo=Mock(); nuevo.poll.return_value=None
        a._servidor=anterior; a._gpu_servidor=False; a.rapido=True
        s=Mock(); s.get.return_value.status_code=200; s.get.return_value.json.return_value={'status':'ok'}
        with patch('coach.draft.whisper_residente.subprocess.Popen',return_value=nuevo) as abrir:
            a.iniciar(a.ticket(),s); a.iniciar(a.ticket(),s)
            anterior.kill.assert_called_once(); abrir.assert_called_once()
            self.assertIn('--no-fallback',abrir.call_args.args[0])
        a.cerrar()
