"""Recortes experimentales del draft visible. Sin reconocimiento ni consejos.

Calibración inicial: capturas de práctica de 2048 x 857, interfaz centrada.
Las coordenadas son hipótesis fuera de esa configuración.
"""
from dataclasses import dataclass
from math import isfinite
from PIL import Image, ImageGrab


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    ancho: int
    alto: int

    @property
    def caja(self):
        return (self.x, self.y, self.x + self.ancho, self.y + self.alto)


# Coordenadas de referencia en una representación de 1914 x 800.
# Se evita la franja inferior donde aparecen nombres de jugadores.
_BASE = {
    **{f'izquierda_{i+1}': (405 + 92*i, 5, 480 + 92*i, 47) for i in range(5)},
    **{f'derecha_{i+1}': (1065 + 92*i, 5, 1140 + 92*i, 47) for i in range(5)},
    'temporizador': (900, 5, 1015, 65),
    'cuadricula': (338, 130, 1218, 530),
}


def regiones(ancho, alto, escala_ui=1.0):
    """Proyecta regiones; rechaza geometrías que quedarían fuera de la imagen."""
    if type(ancho) is not int or type(alto) is not int or ancho <= 0 or alto <= 0:
        raise ValueError('Dimensiones invalidas')
    if not isinstance(escala_ui, (int, float)) or isinstance(escala_ui, bool) or not isfinite(escala_ui) or not 0.5 <= escala_ui <= 1.5:
        raise ValueError('Escala de interfaz invalida')
    escala = alto / 800 * escala_ui
    resultado = {}
    for nombre, (x0, y0, x1, y1) in _BASE.items():
        a = round(ancho / 2 + (x0 - 957) * escala)
        b = round(y0 * escala)
        c = round(ancho / 2 + (x1 - 957) * escala)
        d = round(y1 * escala)
        if not (0 <= a < c <= ancho and 0 <= b < d <= alto):
            raise ValueError('Region fuera de pantalla: ' + nombre)
        resultado[nombre] = Region(a, b, c-a, d-b)
    return resultado


def recortar(imagen, escala_ui=1.0):
    """Procesamiento local de una captura suministrada; no guarda ni transmite."""
    if not isinstance(imagen, Image.Image):
        raise TypeError('Se requiere una imagen Pillow')
    return {nombre: imagen.crop(region.caja) for nombre, region in regiones(*imagen.size, escala_ui).items()}


def capturar_practica(region_pantalla, *, practica_confirmada=False):
    """Captura puntual, voluntaria, en Windows. Sin bucle ni acceso al cliente.

    La región debe ser el rectángulo físico del área de juego en el escritorio.
    La confirmación manual no certifica la modalidad real de la partida.
    """
    if practica_confirmada is not True:
        raise PermissionError('Captura deshabilitada sin confirmacion de practica')
    if not isinstance(region_pantalla, Region) or any(type(v) is not int for v in region_pantalla.caja) or region_pantalla.ancho <= 0 or region_pantalla.alto <= 0:
        raise ValueError('Region de captura invalida')
    imagen = ImageGrab.grab(bbox=region_pantalla.caja, all_screens=True)
    if imagen.size != (region_pantalla.ancho, region_pantalla.alto):
        raise RuntimeError('Dimensiones de captura inesperadas')
    return imagen
