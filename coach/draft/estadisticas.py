"""Importacion offline de enfrentamientos OpenDota; no implica datos ranked actuales."""
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Mapping


@dataclass(frozen=True)
class Enfrentamiento:
    heroe_id: int
    enemigo_id: int
    partidas: int
    victorias: int

    @property
    def tasa(self):
        return self.victorias / self.partidas if self.partidas else None


@dataclass(frozen=True)
class MuestraEnfrentamientos:
    heroe_id: int
    fuente: str
    obtenido_utc: str
    filas: tuple[Enfrentamiento, ...]
    poblacion: str = 'no_verificada_en_payload'
    parche: str | None = None


def importar_opendota(datos, *, heroe_id, catalogo, obtenido_utc):
    """Acepta el JSON de /heroes/{id}/matchups. No inventa parche, rol ni sinergia."""
    if type(heroe_id) is not int or catalogo.por_id(heroe_id) is None:
        raise ValueError('Heroe de origen invalido')
    try:
        fecha = datetime.fromisoformat(obtenido_utc.replace('Z', '+00:00'))
        if fecha.utcoffset() is None or fecha.utcoffset().total_seconds() != 0:
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise ValueError('Fecha UTC invalida') from None
    if not isinstance(datos, list):
        raise ValueError('Respuesta de enfrentamientos invalida')
    filas, vistos = [], set()
    for dato in datos:
        if not isinstance(dato, Mapping):
            raise ValueError('Fila invalida')
        enemigo, partidas, victorias = (dato.get(k) for k in ('hero_id', 'games_played', 'wins'))
        if (any(type(v) is not int for v in (enemigo, partidas, victorias))
                or catalogo.por_id(enemigo) is None or enemigo == heroe_id or enemigo in vistos
                or partidas < 0 or not 0 <= victorias <= partidas):
            raise ValueError('Enfrentamiento invalido o duplicado')
        vistos.add(enemigo)
        filas.append(Enfrentamiento(heroe_id, enemigo, partidas, victorias))
    return MuestraEnfrentamientos(heroe_id, f'https://api.opendota.com/api/heroes/{heroe_id}/matchups',
                                 obtenido_utc, tuple(sorted(filas, key=lambda f: f.enemigo_id)))
