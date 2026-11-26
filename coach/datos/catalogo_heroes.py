"""Importacion offline del catalogo publico de Valve. No consulta al cliente."""
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import hashlib
import os
import tempfile

FUENTE = 'https://www.dota2.com/datafeed/herolist?language=spanish'

@dataclass(frozen=True)
class Heroe:
    id: int
    clave: str
    nombre: str
    atributo: int | None
    complejidad: int | None


def entero_opcional(valor, permitidos):
    return valor if type(valor) is int and valor in permitidos else None


def importar_heroes(datos):
    try:
        filas = datos['result']['data']['heroes']
    except (KeyError, TypeError):
        raise ValueError('Estructura de catalogo desconocida') from None
    if not isinstance(filas, list) or not filas:
        raise ValueError('Catalogo vacio o invalido')
    ids, claves, heroes = set(), set(), []
    for fila in filas:
        if not isinstance(fila, dict):
            raise ValueError('Heroe invalido')
        ident, clave, nombre = (fila.get(k) for k in ('id', 'name', 'name_loc'))
        if (type(ident) is not int or ident <= 0 or not isinstance(clave, str)
                or not re.fullmatch(r'npc_dota_hero_[a-z0-9_]+', clave)
                or not isinstance(nombre, str) or not nombre.strip()):
            raise ValueError('Identidad de heroe invalida')
        if ident in ids or clave in claves:
            raise ValueError('Identidad de heroe duplicada')
        ids.add(ident)
        claves.add(clave)
        heroes.append(Heroe(ident, clave, nombre.strip(),
                            entero_opcional(fila.get('primary_attr'), range(4)),
                            entero_opcional(fila.get('complexity'), range(1, 4))))
    return tuple(sorted(heroes, key=lambda h: h.id))


class CatalogoHeroes:
    def __init__(self, heroes):
        self.heroes = tuple(heroes)
        self._ids = {h.id: h for h in self.heroes}
        self._claves = {h.clave: h for h in self.heroes}

    def por_id(self, ident):
        return self._ids.get(ident) if type(ident) is int else None

    def por_clave(self, clave):
        return self._claves.get(clave) if isinstance(clave, str) else None


def guardar_catalogo(origen, destino, parche_referencia):
    """El parche es una etiqueta aportada por el operador, no verificada por el feed."""
    if not isinstance(parche_referencia, str) or not re.fullmatch(r'\d+\.\d+[a-z]?', parche_referencia):
        raise ValueError('Parche de referencia invalido')
    bruto = Path(origen).read_bytes()
    heroes = importar_heroes(json.loads(bruto.decode('utf-8-sig')))
    resultado = {'esquema': 1, 'fuente_declarada': FUENTE,
                 'parche_referencia': parche_referencia, 'parche_verificado': False,
                 'importado_utc': datetime.now(timezone.utc).isoformat(),
                 'sha256_origen': hashlib.sha256(bruto).hexdigest(),
                 'heroes': [vars(h) for h in heroes]}
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, temporal = tempfile.mkstemp(dir=destino.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as archivo:
            json.dump(resultado, archivo, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temporal, destino)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
    return CatalogoHeroes(heroes)
