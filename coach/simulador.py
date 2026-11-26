"""Reproducción offline de JSONL GSI, sin red, voz ni cliente Dota.
Uso de desarrollo: python -m coach.simulador archivo.jsonl --practica
La marca practica autoriza exclusivamente esta simulación offline.
"""
from collections import Counter
from dataclasses import dataclass, field
import argparse
import json
import math
from .state import EstadoPartida, parsear
from .eventos_avanzados import detectar_avanzados
from .prioridades import ControlAvisos
from .ai.contexto import construir_contexto, respuesta_vigente, preparar_respuesta


@dataclass
class Resumen:
    mensajes: int = 0
    eventos: Counter = field(default_factory=Counter)
    intervenciones: Counter = field(default_factory=Counter)
    solicitudes: int = 0
    respuestas_aceptadas: int = 0
    respuestas_descartadas: int = 0
    pendientes_al_final: int = 0
    duracion: float = 0.0

    def publico(self):
        return dict(mensajes=self.mensajes, eventos=dict(self.eventos),
                    intervenciones=dict(self.intervenciones), solicitudes=self.solicitudes,
                    respuestas_aceptadas=self.respuestas_aceptadas,
                    respuestas_descartadas=self.respuestas_descartadas,
                    pendientes_al_final=self.pendientes_al_final,
                    duracion=round(self.duracion, 3))


def _tiempo(v):
    return type(v) in (int, float) and math.isfinite(v)


def reproducir(lineas, *, practica=False, demora=2.0, respuesta='Revisa tu situación antes de actuar.'):
    """Una sesión independiente. La respuesta fija es ficticia, no un consejo real.
    Evalúa respuestas vencidas antes del siguiente POST usando el último estado;
    si coinciden temporalmente con un POST, primero procesa el nuevo estado.
    No simula datos después del último POST. Rechaza registros corruptos.
    """
    if not _tiempo(demora) or demora < 0 or demora > 3600:
        raise ValueError('Demora inválida')
    resumen = Resumen()
    control = ControlAvisos()
    anterior = EstadoPartida()
    inicio = ultimo = None
    pendiente = None

    def entregar(estado, ahora, edad):
        nonlocal pendiente
        solicitud, _ = pendiente
        if (respuesta_vigente(solicitud, estado, ahora, practica=practica, edad_estado=edad)
                and preparar_respuesta(respuesta, solicitud) is not None):
            resumen.respuestas_aceptadas += 1
        else:
            resumen.respuestas_descartadas += 1
        pendiente = None

    for numero, linea in enumerate(lineas, 1):
        if not linea.strip():
            continue
        try:
            registro = json.loads(linea)
            if not isinstance(registro, dict) or not _tiempo(registro.get('t')) or not isinstance(registro.get('datos'), dict):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(f'Registro inválido en línea {numero}') from None
        marca = registro['t']
        if inicio is None:
            inicio = marca
        ahora = marca - inicio
        if not _tiempo(ahora) or (ultimo is not None and ahora < ultimo):
            raise ValueError(f'Reloj inválido en línea {numero}')
        if pendiente and pendiente[1] < ahora:
            vencimiento = pendiente[1]
            entregar(anterior, vencimiento, vencimiento - ultimo)
        estado = parsear(registro['datos'])
        if pendiente and pendiente[1] <= ahora:
            entregar(estado, ahora, 0)
        eventos = detectar_avanzados(anterior, estado)
        resumen.eventos.update(e.tipo for e in eventos)
        intervencion = control.seleccionar(eventos, estado, ahora, practica=practica,
                                          ia_disponible=True, ia_ocupada=pendiente is not None)
        if intervencion:
            resumen.intervenciones[intervencion.tipo] += 1
            if intervencion.usa_ia:
                solicitud = construir_contexto(estado, intervencion, ahora, practica=practica)
                if solicitud:
                    resumen.solicitudes += 1
                    pendiente = (solicitud, ahora + demora)
                    if demora == 0:
                        entregar(estado, ahora, 0)
        anterior, ultimo = estado, ahora
        resumen.mensajes += 1
        resumen.duracion = ahora
    resumen.pendientes_al_final = int(pendiente is not None)
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo')
    parser.add_argument('--practica', action='store_true')
    parser.add_argument('--demora', type=float, default=2.0)
    args = parser.parse_args()
    try:
        with open(args.archivo, encoding='utf-8-sig') as f:
            resumen = reproducir(f, practica=args.practica, demora=args.demora)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(resumen.publico(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
