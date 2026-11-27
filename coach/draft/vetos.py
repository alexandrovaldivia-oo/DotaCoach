"""Diagnóstico offline de marcas de veto en casillas previamente calibradas.
No identifica héroes ni certifica disponibilidad; no captura la pantalla.
"""
from dataclasses import dataclass
from PIL import Image

@dataclass(frozen=True)
class MarcaVeto:
    estado: str
    cobertura: float
    contraste: float


def detectar_marca(imagen):
    """Busca una banda roja continua ascendente sobre una casilla vertical.
    Los umbrales son experimentales. Una ausencia no implica disponibilidad.
    """
    if not isinstance(imagen, Image.Image) or min(imagen.size) < 12:
        raise ValueError('Casilla invalida')
    im = imagen.convert('RGB').resize((40, 60), Image.Resampling.BILINEAR)
    def rojo(x,y):
        r,g,b = im.getpixel((x,y))
        return r >= 48 and r-g >= 13 and r-b >= 8 and r >= 1.19*g
    mejor = (0.,0.)
    for pendiente in (.45,.55,.65,.75,.85):
        for centro in range(14,27,2):
            hits = fondo = 0
            for y in range(5,55):
                x = round(centro + (30-y)*pendiente)
                hits += any(rojo(k,y) for k in range(max(0,x-2),min(40,x+3)))
                vecinos = [k for k in (x-7,x+7) if 0<=k<40]
                fondo += sum(rojo(k,y) for k in vecinos)/max(1,len(vecinos))
            cobertura, contraste = hits/50, (hits-fondo)/50
            if cobertura + contraste > sum(mejor):
                mejor = cobertura, contraste
    c,d = mejor
    estado = 'marca_probable' if c >= .84 and d >= .60 else 'dudosa' if c >= .60 and d >= .30 else 'sin_marca_detectada'
    return MarcaVeto(estado,c,d)


def analizar_casillas(imagen, regiones):
    """Regiones explícitas de una captura guardada, sin inferir orden de héroes."""
    if not isinstance(imagen, Image.Image):
        raise ValueError('Imagen invalida')
    salida = {}
    for clave, caja in regiones.items():
        if len(caja)!=4 or any(type(v) is not int for v in caja):
            raise ValueError('Region invalida')
        x,y,z,w = caja
        if not (0<=x<z<=imagen.width and 0<=y<w<=imagen.height):
            raise ValueError('Region fuera de imagen')
        salida[clave] = detectar_marca(imagen.crop(caja))
    return salida
