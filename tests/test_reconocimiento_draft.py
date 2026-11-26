import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw, ImageEnhance
from coach.draft.reconocimiento import ReconocedorRetratos


def dibujo(tipo):
    im=Image.new('RGB',(96,54),'#253343')
    d=ImageDraw.Draw(im)
    if tipo==0:
        d.rectangle((5,5,43,48),fill='red');d.ellipse((55,8,87,47),fill='yellow')
    else:
        d.rectangle((5,5,90,24),fill='blue');d.ellipse((20,30,70,49),fill='cyan')
    return im


def biblioteca(ruta, *, identicos=False, incompleta=False):
    with ZipFile(ruta,'w') as z:
        z.writestr('heroes_valve.json',json.dumps({'result':{'data':{'heroes':[{'name':'npc_dota_hero_alfa'},{'name':'npc_dota_hero_beta'}]}}}))
        for i,n in enumerate(('alfa','beta')):
            for v in ('horizontal','legacy'):
                if incompleta and i==1 and v=='legacy':continue
                b=io.BytesIO(); dibujo(0 if identicos else i).save(b,format='PNG');z.writestr(f'{v}/{n}.png',b.getvalue())


class TestReconocimiento(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ruta=Path(self.tmp.name)/'refs.zip';biblioteca(self.ruta)
        self.r=ReconocedorRetratos(self.ruta)
    def test_identidad(self):
        self.assertEqual(self.r.reconocer(dibujo(0)).heroe,'alfa')
        self.assertEqual(self.r.reconocer(dibujo(1)).heroe,'beta')
    def test_luminosidad(self):
        self.assertEqual(self.r.reconocer(ImageEnhance.Brightness(dibujo(0)).enhance(.5)).heroe,'alfa')
    def test_resolucion(self):
        self.assertEqual(self.r.reconocer(dibujo(1).resize((48,27))).heroe,'beta')
    def test_uniforme(self):
        self.assertIsNone(self.r.reconocer(Image.new('RGB',(96,54),'gray')).heroe)
    def test_ambiguo(self):
        biblioteca(self.ruta,identicos=True)
        self.assertIsNone(ReconocedorRetratos(self.ruta).reconocer(dibujo(0)).heroe)
    def test_incompleta(self):
        biblioteca(self.ruta,incompleta=True)
        with self.assertRaises(KeyError):ReconocedorRetratos(self.ruta)
    def test_recorte(self):
        res=self.r.reconocer_captura(Image.new('RGB',(2048,857),'black'))
        self.assertEqual(len(res),10);self.assertTrue(all(v.heroe is None for v in res.values()))
    def test_umbral(self):
        with self.assertRaises(ValueError):ReconocedorRetratos(self.ruta,umbral=0)
