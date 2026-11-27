"""Comparación experimental de retratos en capturas guardadas de ranked.

No captura pantalla, no confirma selecciones ni emite recomendaciones.
Una coincidencia aceptada es solo una identidad visual candidata.
"""
from array import array
from io import BytesIO
from itertools import product
import json
import math
from operator import mul
from zipfile import ZipFile
from PIL import Image
from .captura import regiones
from .estado import CASILLAS
from .reconocimiento import Coincidencia, _NOMBRE

# Ventanas parciales de referencia para compensar la franja de rango.
_VENTANAS = tuple((l,t,r,b) for l,r,t,b in product(
    (.05,.15,.25), (.75,.85,.95), (0,.08,.16,.24), (.45,.55,.65,.75))
    if r-l >= .5)


def _firma(imagen):
    rgb = imagen.convert('RGB').resize((16,8), Image.Resampling.BICUBIC)
    datos = list(rgb.get_flattened_data() if hasattr(rgb, 'get_flattened_data') else rgb.getdata())
    medias = [sum(p[c] for p in datos)/len(datos) for c in range(3)]
    v = [p[c]-medias[c] for p in datos for c in range(3)]
    norma = math.sqrt(sum(x*x for x in v))
    # Usar cromaticidad absoluta como filtro auxiliar, no como prueba de pick.
    chroma = sum(max(p)-min(p) for p in datos)/len(datos)
    return (array('f',(x/norma for x in v)) if norma > 1e-8 else None, chroma)


def bandas_ranked(imagen, escala_ui=1.0):
    """Banda central superior que excluye gran parte de la medalla y el rango."""
    if not isinstance(imagen, Image.Image):
        raise TypeError('Se requiere una imagen Pillow')
    regiones(*imagen.size, escala_ui)
    s = imagen.height / 800 * escala_ui
    salida = {}
    for k in CASILLAS:
        # Centro de la región original; evita bordes inclinados.
        x = imagen.width / 2 + ((405 if k.startswith('izquierda') else 1065)
            + 92*(int(k.rsplit('_',1)[1])-1)-957)*s
        caja = (round(x+8*s), round(6*s), round(x+64*s), round(32*s))
        if not (0 <= caja[0] < caja[2] <= imagen.width and 0 <= caja[1] < caja[3] <= imagen.height):
            raise ValueError('Banda fuera de imagen')
        salida[k] = imagen.crop(caja)
    return salida


class ReconocedorRanked:
    """Reconocedor offline; umbrales calibrados en una sola partida ranked."""
    def __init__(self, ruta_zip, *, umbral=.75, margen=.15, cromaticidad_minima=24., proporcion_color=.75):
        if not (0 < umbral <= 1 and 0 < margen <= 1 and 0 <= cromaticidad_minima <= 255 and 0 < proporcion_color <= 1):
            raise ValueError('Umbrales invalidos')
        self.umbral, self.margen = umbral, margen
        self.cromaticidad_minima = cromaticidad_minima
        self.proporcion_color = proporcion_color
        self._refs = []
        with ZipFile(ruta_zip) as z:
            entradas = {}
            for info in z.infolist():
                n = info.filename.replace('\\','/')
                if n in entradas:
                    raise ValueError('Entrada duplicada')
                entradas[n] = info
            def leer(n, limite):
                info = entradas[n]
                if info.file_size > limite:
                    raise ValueError('Recurso demasiado grande')
                return z.read(info)
            heroes = json.loads(leer('heroes_valve.json',1000000).decode('utf-8-sig'))['result']['data']['heroes']
            nombres = set()
            for h in heroes:
                nombre = h['name']
                if not nombre.startswith('npc_dota_hero_'):
                    raise ValueError('Identificador invalido')
                clave = nombre[len('npc_dota_hero_'):]
                if not _NOMBRE.fullmatch(clave) or clave in nombres:
                    raise ValueError('Nombre invalido o duplicado')
                nombres.add(clave)
                for variante in ('horizontal','legacy'):
                    with Image.open(BytesIO(leer(f'{variante}/{clave}.png',4000000))) as im:
                        if im.format != 'PNG' or not (16 <= im.width <= 2048 and 16 <= im.height <= 2048):
                            raise ValueError('Imagen invalida')
                        w,h = im.size
                        for l,t,r,b in _VENTANAS:
                            v,c = _firma(im.crop((int(l*w),int(t*h),int(r*w),int(b*h))))
                            if v is not None:
                                self._refs.append((clave,v,c))
            if len(nombres)<2 or {n for n,_,_ in self._refs} != nombres:
                raise ValueError('Biblioteca incompleta o sin textura')
        self.cantidad_heroes = len(nombres)

    def reconocer(self, banda):
        if not isinstance(banda,Image.Image) or min(banda.size)<8:
            raise ValueError('Banda invalida')
        v,c = _firma(banda)
        if v is None or c < self.cromaticidad_minima:
            return Coincidencia(None,0.,0.)
        mejores = {}
        for nombre,ref,color in self._refs:
            score = sum(map(mul,v,ref))
            if nombre not in mejores or score > mejores[nombre][0]:
                mejores[nombre] = (score,color)
        orden = sorted(mejores.items(),key=lambda p:(-p[1][0],p[0]))
        nombre,(score,color) = orden[0]
        margen = score-orden[1][1][0]
        valido = (score >= self.umbral and margen >= self.margen
                  and c >= color*self.proporcion_color)
        return Coincidencia(nombre if valido else None,score,margen)

    def reconocer_captura(self, imagen, escala_ui=1.0):
        return {k:self.reconocer(v) for k,v in bandas_ranked(imagen,escala_ui).items()}
