"""Constantes del juego que CAMBIAN con los parches.
Revisar en cada parche. Estan aqui aparte para no esconderlas en la logica."""

# Runa de sabiduria: cada 7 minutos (se avisa unos segundos antes).
SABIDURIA_INTERVALO = 7 * 60
SABIDURIA_AVISO_ANTES = 30
SABIDURIA_MAXIMO_CICLOS = 8

# Tormentor: aparicion segun tu proyecto anterior (verificar con el parche actual).
TORMENTOR_APARICION = 20 * 60
TORMENTOR_AVISO_ANTES = 30

# Niveles en los que se desbloquea la definitiva de la mayoria de heroes.
NIVELES_DEFINITIVA = (6, 12, 18)
