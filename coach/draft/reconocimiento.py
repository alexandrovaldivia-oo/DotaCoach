"""Reconocimiento experimental local de retratos, sin captura ni consejos.

Las puntuaciones son similitudes, no probabilidades. Una identidad reconocida
no demuestra que la selección esté confirmada. Biblioteca ZIP local del usuario.
"""
from dataclasses import dataclass
from io import BytesIO
import json
import math
import re
from zipfile import ZipFile
from PIL import Image
from .captura import recortar

_RECORTES = ((0,0,1,1), (.05,.05,.95,.95), (.08,.08,.92,.92),
             (.1,0,.9,.9), (.08,0,.92,.85), (.15,.05,.85,.9))
_NOMBRE = re.compile(r'[a-z0-9_]+\Z')


def _vector(imagen):
    pixeles = list(imagen.convert('RGB').resize((24,14), Image.Resampling.BICUBIC).getdata())
    medias = tuple(sum(p[c] for p in pixeles)/len(pixeles) for c in range(3))
    v = tuple(p[c]-medias[c] for p in pixeles for c in range(3))
    norma = math.sqrt(sum(x*x for x in v))
    return tuple(x/norma for x in v) if norma > 1e-8 else None


@dataclass(frozen=True)
class Coincidencia:
    heroe: str | None
    similitud: float
    margen: float


class ReconocedorRetratos:
    def __init__(self, ruta_zip, *, umbral=.75, margen=.15):
        if not (0 < umbral <= 1 and 0 < margen <= 1):
            raise ValueError('Umbrales invalidos')
        self.umbral, self.margen = umbral, margen
        self._referencias = []
        with ZipFile(ruta_zip) as z:
            entradas = {}
            for info in z.infolist():
                nombre = info.filename.replace('\\','/')
                if nombre in entradas:
                    raise ValueError('Entrada duplicada')
                entradas[nombre] = info
            def leer(nombre, limite):
                info = entradas[nombre]
                if info.file_size > limite:
                    raise ValueError('Recurso demasiado grande')
                return z.read(info)
            catalogo = json.loads(leer('heroes_valve.json', 1000000).decode('utf-8-sig'))
            heroes = catalogo['result']['data']['heroes']
            nombres = set()
            for hero in heroes:
                nombre = hero['name']
                if not nombre.startswith('npc_dota_hero_'):
                    raise ValueError('Identificador invalido')
                corto = nombre[len('npc_dota_hero_'):]
                if not _NOMBRE.fullmatch(corto) or corto in nombres:
                    raise ValueError('Nombre invalido o duplicado')
                nombres.add(corto)
                for variante in ('horizontal','legacy'):
                    with Image.open(BytesIO(leer(f'{variante}/{corto}.png', 4000000))) as im:
                        if im.format != 'PNG' or not (16 <= im.width <= 2048 and 16 <= im.height <= 2048):
                            raise ValueError('Imagen invalida')
                        for l,t,r,b in _RECORTES:
                            v = _vector(im.crop((int(l*im.width),int(t*im.height),int(r*im.width),int(b*im.height))))
                            if v is not None:
                                self._referencias.append((corto,v))
            if len(nombres) < 2 or {n for n,_ in self._referencias} != nombres:
                raise ValueError('Biblioteca incompleta o sin textura')
        self.cantidad_heroes = len(nombres)

    def reconocer(self, imagen):
        if not isinstance(imagen, Image.Image) or min(imagen.size)<8:
            raise ValueError('Recorte invalido')
        v = _vector(imagen)
        if v is None:
            return Coincidencia(None,0.,0.)
        mejores = {}
        for nombre,ref in self._referencias:
            score = sum(a*b for a,b in zip(v,ref))
            mejores[nombre] = max(mejores.get(nombre,-1.),score)
        orden = sorted(mejores.items(), key=lambda par: (-par[1],par[0]))
        nombre,score = orden[0]
        margen = score-orden[1][1]
        return Coincidencia(nombre if score>=self.umbral and margen>=self.margen else None,score,margen)

    def reconocer_captura(self, imagen, escala_ui=1.0):
        return {k:self.reconocer(v) for k,v in recortar(imagen,escala_ui).items()
                if k.startswith(('izquierda_','derecha_'))}
