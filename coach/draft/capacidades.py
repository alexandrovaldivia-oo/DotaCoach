"""Perfiles parciales para estudio offline; no habilita recomendaciones en partida."""
from dataclasses import dataclass
from types import MappingProxyType
from datetime import date

CAPACIDADES = frozenset('dano_fisico dano_magico dano_puro iniciacion aturdimiento silencio movilidad escape supervivencia estructuras oleadas escalamiento proteccion habilidad_condicional'.split())

@dataclass(frozen=True)
class Evidencia:
    capacidad: str
    estado: str
    detalle: str
    fuente: str
    revisado: str
    parche: str | None = None

@dataclass(frozen=True)
class Perfil:
    heroe_id: int
    evidencias: tuple[Evidencia, ...]

    def estado(self, capacidad):
        if capacidad not in CAPACIDADES:
            raise ValueError('Capacidad desconocida')
        return next((e.estado for e in self.evidencias if e.capacidad == capacidad), 'desconocido')


def validar_perfiles(perfiles, catalogo):
    resultado = {}
    for perfil in perfiles:
        if type(perfil.heroe_id) is not int or catalogo.por_id(perfil.heroe_id) is None or perfil.heroe_id in resultado:
            raise ValueError('Identidad invalida o duplicada')
        vistos = set()
        for e in perfil.evidencias:
            if e.capacidad not in CAPACIDADES or e.capacidad in vistos or e.estado not in ('documentado', 'condicional', 'inferido'):
                raise ValueError('Evidencia invalida o duplicada')
            if not e.detalle.strip() or not e.fuente.startswith('https://www.dota2.com/hero/'):
                raise ValueError('Evidencia sin fuente oficial')
            date.fromisoformat(e.revisado)
            vistos.add(e.capacidad)
        resultado[perfil.heroe_id] = perfil
    return MappingProxyType(resultado)


def consultar(perfiles, catalogo, heroe_id):
    if catalogo.por_id(heroe_id) is None:
        raise ValueError('Heroe desconocido')
    return perfiles.get(heroe_id, Perfil(heroe_id, ()))


def _e(capacidad, estado, detalle, slug):
    return Evidencia(capacidad, estado, detalle, 'https://www.dota2.com/hero/' + slug, '2026-11-27')

# Evidencia parcial: no certifica el parche ni ausencia de otras capacidades.
PILOTO = (
    Perfil(39, (_e('movilidad', 'documentado', 'Dispone de Traslacion.', 'queenofpain'),
                _e('escape', 'inferido', 'La traslacion puede servir para retirarse si esta disponible.', 'queenofpain'))),
    Perfil(13, (_e('aturdimiento', 'condicional', 'La ruptura del vinculo de su definitiva puede aturdir al enemigo.', 'puck'),)),
    Perfil(86, (_e('habilidad_condicional', 'condicional', 'Puede robar habilidades enemigas elegibles; su aporte depende del hechizo obtenido.', 'rubick'),)),
)
