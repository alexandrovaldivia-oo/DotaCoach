import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from coach.gsi import setup
from coach.gsi.grabador import GrabadorGSI

class PruebasConfiguracionGSI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def instalar(self, nombre, exe=True):
        base = self.base / nombre
        cfg = base / setup.SUBRUTA_DOTA
        cfg.mkdir(parents=True)
        if exe:
            binario = cfg.parent.parent / 'bin' / 'win64' / 'dota2.exe'
            binario.parent.mkdir(parents=True)
            binario.touch()
        return base, cfg

    def test_ignora_instalacion_incompleta(self):
        a, _ = self.instalar('antigua', False)
        b, cfg = self.instalar('activa')
        with patch.object(setup, '_bibliotecas_steam', return_value=[str(a), str(b)]):
            self.assertEqual(setup.encontrar_carpeta_cfg(), str(cfg))

    def test_no_adivina_entre_dos_instalaciones(self):
        a, _ = self.instalar('a')
        b, cfg = self.instalar('b')
        with patch.object(setup, '_bibliotecas_steam', return_value=[str(a), str(b)]):
            with self.assertRaises(OSError):
                setup.encontrar_carpeta_cfg()
            self.assertEqual(setup.encontrar_carpeta_cfg(str(cfg)), str(cfg))

    def test_cfg_validado_y_respaldo(self):
        _, cfg = self.instalar('activa')
        destino = Path(setup.crear_cfg(4125, ruta_cfg=str(cfg)))
        texto = destino.read_text()
        self.assertIn('http://127.0.0.1:4125/', texto)
        self.assertIn('"heartbeat"     "10.0"', texto)
        for campo in ('provider','map','player','hero','abilities','items'):
            self.assertIn('"'+campo+'"', texto)
        for campo in ('events','draft','buildings','league','wearables'):
            self.assertNotIn('"'+campo+'"', texto)
        setup.crear_cfg(4125, ruta_cfg=str(cfg))
        self.assertEqual(list(destino.parent.glob('*.bak')), [])
        setup.crear_cfg(4126, ruta_cfg=str(cfg))
        respaldos = list(destino.parent.glob('*.bak'))
        self.assertEqual(len(respaldos), 1)
        self.assertEqual(respaldos[0].read_text(), texto)

    def test_catalogo_sin_cerrar_programa(self):
        g = GrabadorGSI(self.tmp.name)
        g({'hero': {'level': 3}})
        self.assertIn('hero.level', Path(g.ruta_campos).read_text())
        self.assertEqual(g.mensajes, 1)
        g({'map': {'clock_time': 10}})
        g.cerrar()
        self.assertIn('map.clock_time', Path(g.ruta_campos).read_text())
