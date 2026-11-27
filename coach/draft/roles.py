"""Reconocimiento experimental offline de bandas de rol en español.
No identifica la casilla propia ni confirma la modalidad o el turno.
"""
from dataclasses import dataclass
from pathlib import Path
from math import sqrt
from PIL import Image
from .diagnostico_ranked import recortes_ranked
from .estado import ROLES

@dataclass(frozen=True)
class RolVisual:
    rol: int | None
    similitud: float
    margen: float


def _mascara(imagen):
    if not isinstance(imagen, Image.Image) or min(imagen.size) < 4:
        raise ValueError('Banda de rol invalida')
    gris = imagen.convert('L').resize((100, 26), Image.Resampling.BILINEAR)
    return gris.point(lambda p: max(0, p-90))


def _vector(imagen):
    return tuple(imagen.tobytes())


def _sim(a, b):
    den = sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    return sum(x*y for x,y in zip(a,b))/den if den else 0.0


class ReconocedorRoles:
    def __init__(self, carpeta=None):
        carpeta = Path(carpeta) if carpeta is not None else Path(__file__).with_name('recursos_roles')
        self.plantillas = {}
        for rol in ROLES:
            with Image.open(carpeta / f'rol_{rol}.png') as im:
                mask = _mascara(im)
            variantes = []
            for dx in range(-7,8):
                for dy in range(-3,4):
                    desplazada = Image.new('L', mask.size)
                    desplazada.paste(mask, (dx,dy))
                    variantes.append(_vector(desplazada))
            self.plantillas[rol] = variantes

    def reconocer(self, imagen):
        mask = _mascara(imagen)
        v = _vector(mask)
        if sum(p > 20 for p in v) < 35:
            return RolVisual(None, 0.0, 0.0)
        resultados = sorted(((max(_sim(v,t) for t in ts), r) for r,ts in self.plantillas.items()), reverse=True)
        mejor, rol = resultados[0]
        margen = mejor-resultados[1][0]
        return RolVisual(rol if mejor >= .72 and margen >= .09 else None, mejor, margen)

    def analizar(self, imagen, escala_ui=1.0):
        return {k:self.reconocer(v['rol']) for k,v in recortes_ranked(imagen, escala_ui).items()}
