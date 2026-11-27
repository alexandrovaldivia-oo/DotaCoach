"""Asociación offline de casillas a referencias anotadas de una cuadrícula limpia.
No captura pantalla, no infiere orden ni disponibilidad y no emite consejos.
"""
from dataclasses import dataclass
from math import sqrt, isfinite
from PIL import Image, ImageOps
from .vetos import detectar_marca

@dataclass(frozen=True)
class CasillaIdentificada:
    heroe_id: int | None
    similitud: float
    margen: float
    marca: str


def _firma(imagen):
    if not isinstance(imagen, Image.Image) or min(imagen.size) < 12:
        raise ValueError('Casilla invalida')
    im = ImageOps.grayscale(imagen).resize((12, 20), Image.Resampling.BILINEAR)
    # Excluir banda diagonal central para reducir interferencia de vetos.
    datos = [im.getpixel((x, y)) for y in range(2, 17) for x in range(1, 11)
             if abs(x - (6 + (10-y)*.38)) > 2]
    media = sum(datos)/len(datos)
    v = [x-media for x in datos]
    norma = sqrt(sum(x*x for x in v))
    return tuple(x/norma for x in v) if norma > 1e-8 else None


def recortar_cuadricula(imagen, cajas):
    """Cajas explícitas calibradas para esta imagen; claves arbitrarias de casilla."""
    if not isinstance(imagen, Image.Image):
        raise ValueError('Imagen invalida')
    resultado = {}
    for k, caja in cajas.items():
        if len(caja) != 4 or any(type(n) is not int for n in caja):
            raise ValueError('Caja invalida')
        x,y,z,w = caja
        if not (0 <= x < z <= imagen.width and 0 <= y < w <= imagen.height):
            raise ValueError('Caja fuera de imagen')
        resultado[k] = imagen.crop(caja)
    return resultado


class ReconocedorCuadricula:
    def __init__(self, referencias, catalogo, *, umbral=.82, margen=.12):
        if not all(type(v) in (int,float) and isfinite(v) and 0 < v <= 1 for v in (umbral,margen)):
            raise ValueError('Umbrales invalidos')
        ids = {h.id for h in catalogo.heroes}
        if len(ids) < 2 or set(referencias) != ids or any(type(k) is not int for k in referencias):
            raise ValueError('Referencias incompletas o invalidas')
        self._refs = {k:_firma(im) for k,im in referencias.items()}
        if any(v is None for v in self._refs.values()):
            raise ValueError('Referencia sin textura')
        self.umbral, self.margen = umbral,margen

    def reconocer(self, imagen):
        v = _firma(imagen)
        marca = detectar_marca(imagen).estado
        if v is None:
            return CasillaIdentificada(None,0.,0.,marca)
        puntuaciones = sorted(((sum(a*b for a,b in zip(v,r)), k) for k,r in self._refs.items()), reverse=True)
        mejor, ident = puntuaciones[0]
        diferencia = mejor-puntuaciones[1][0]
        return CasillaIdentificada(ident if mejor >= self.umbral and diferencia >= self.margen else None,
                                    mejor,diferencia,marca)

    def analizar(self, casillas):
        resultados = {k:self.reconocer(im) for k,im in casillas.items()}
        ids = [r.heroe_id for r in resultados.values() if r.heroe_id is not None]
        duplicados = {i for i in ids if ids.count(i)>1}
        return {k:CasillaIdentificada(None,r.similitud,r.margen,r.marca) if r.heroe_id in duplicados else r
                for k,r in resultados.items()}


def vetos_probables(resultados):
    """Solo candidatos identificados; nunca una lista completa de vetos."""
    return frozenset(r.heroe_id for r in resultados.values()
                     if r.heroe_id is not None and r.marca == 'marca_probable')
