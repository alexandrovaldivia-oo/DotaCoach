"""Recortes experimentales para estudiar capturas guardadas, no captura en vivo.
No confirma héroes, roles, vetos ni turnos y no genera recomendaciones.
"""
from PIL import Image
from .captura import regiones
from .estado import CASILLAS


def recortes_ranked(imagen, escala_ui=1.0):
    """Separa retrato superior y zona de rol; geometría aún experimental.

    La banda superior excluye gran parte de la superposición del rango.
    La zona de rol se recorta en ambos lados sin presuponer equipo propio.
    """
    if not isinstance(imagen, Image.Image):
        raise TypeError('Se requiere una imagen Pillow')
    zonas = regiones(*imagen.size, escala_ui)
    s = imagen.height / 800 * escala_ui
    salida = {}
    for casilla in CASILLAS:
        r = zonas[casilla]
        margen = round(3 * s)
        superior = (r.x + margen, round(5*s), r.x+r.ancho-margen, round(32*s))
        rol = (r.x, round(80*s), r.x+r.ancho, round(93*s))
        for caja in (superior, rol):
            x0,y0,x1,y1 = caja
            if not (0 <= x0 < x1 <= imagen.width and 0 <= y0 < y1 <= imagen.height):
                raise ValueError('Zona experimental fuera de pantalla')
        salida[casilla] = {'original': imagen.crop(r.caja),
                           'superior': imagen.crop(superior),
                           'rol': imagen.crop(rol)}
    return salida
