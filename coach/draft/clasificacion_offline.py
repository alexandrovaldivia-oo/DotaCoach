"""Resumen descriptivo de escenarios archivados; no predice victorias ni aconseja en vivo."""
from statistics import mean
from .analisis_offline import comparar


def clasificar(*, minimo_partidas=100, **escenario):
    """Orden experimental por media no ponderada de tasas de pares.

    Solo si todos los candidatos tienen las ocho relaciones y muestras suficientes.
    No combina dominio, capacidades ni synergy con la tasa observada.
    """
    if type(minimo_partidas) is not int or minimo_partidas < 1:
        raise ValueError('Minimo de partidas invalido')
    resultado = comparar(**escenario)
    filas = []
    for candidato in resultado['candidatos']:
        relaciones = candidato['relaciones']
        suficientes = [d for _, _, d in relaciones if d is not None and d['partidas'] >= minimo_partidas]
        completa = len(suficientes) == 8
        tasa = mean(d['tasa'] for d in suficientes) if completa else None
        fila = dict(candidato, media_descriptiva=tasa, muestras_suficientes=len(suficientes))
        partes = [f"{fila['nombre']}. {len(suficientes)} de 8 relaciones con muestra suficiente."]
        if tasa is not None:
            partes.append(f"Media descriptiva de tasas observadas: {tasa*100:.2f} por ciento. No es una probabilidad de ganar.")
        else:
            partes.append('Informacion insuficiente para comparar las ocho relaciones.')
        if fila['en_repertorio']:
            partes.append('Incluido en el repertorio personal para la posicion indicada.')
        if fila['evidencias']:
            partes.extend(f"{e.estado}: {e.detalle}" for e in fila['evidencias'])
        else:
            partes.append('Sin perfil estrategico documentado.')
        partes.append('Rango y vigencia no certificados. Solo estudio fuera de partida.')
        fila['explicacion'] = ' '.join(partes)
        filas.append(fila)
    comparable = len(filas) >= 2 and all(f['media_descriptiva'] is not None for f in filas)
    orden = tuple(f['heroe'] for f in sorted(filas, key=lambda f: (-f['media_descriptiva'], f['heroe']))) if comparable else ()
    return dict(resultado, candidatos=tuple(filas), orden_descriptivo=orden,
                comparacion_descriptiva_disponible=comparable, ranking_disponible=False,
                recomendacion_disponible=False, minimo_partidas=minimo_partidas)
