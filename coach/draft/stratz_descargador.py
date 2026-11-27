"""Orquestador offline; red masiva deliberadamente no habilitada."""
import json
from pathlib import Path
from .stratz_cliente import extraer
from .stratz_validador import validar
from .stratz_almacen import AlmacenStratz


def cargar_catalogo(ruta):
    datos = json.loads(Path(ruta).read_text(encoding='utf-8-sig'))['heroes']
    ids = [h['id'] for h in datos]
    if not ids or any(type(i) is not int or i <= 0 for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Catalogo invalido')
    return set(ids)


def importar_archivo(ruta, *, alias, heroe, rango, ids, almacen, semana=None):
    grupo = extraer(json.loads(Path(ruta).read_text(encoding='utf-8-sig')), alias)
    periodo, filas = validar(grupo, heroe, rango, ids, semana)
    almacen.guardar(periodo, rango, heroe, filas)
    return periodo, len(filas)


def descargar_lote(cliente, almacen, *, heroe, rango, ids, semana=None):
    """Una sola consulta por invocacion; el llamador controla cuotas. Sin bucle masivo."""
    if semana is not None and almacen.completo(semana,rango,heroe,ids):
        return semana, 0
    periodo, filas = validar(cliente.consultar(heroe,rango,semana), heroe,rango,ids,semana)
    almacen.guardar(periodo,rango,heroe,filas)
    return periodo,len(filas)
