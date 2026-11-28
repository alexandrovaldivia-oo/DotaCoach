"""Conversación local de estudio; sin red, captura ni acciones sobre el juego."""
import re
from dataclasses import replace
from .contexto_conversacional import Contexto, actualizar, analizar, resolver, normalizar, validar
from .repertorio import cargar_repertorio

REPERTORIO = {1: ('Drow Ranger','Juggernaut','Lifestealer'), 2: ('Queen of Pain','Puck','Rubick'), 3: ('Dawnbreaker','Underlord','Axe'), 4: ('Shadow Demon','Tusk','Rubick'), 5: ('Disruptor','Lion','Crystal Maiden')}

class ChatOffline:
    def __init__(self, catalogo, ruta, semana, rango):
        self.catalogo, self.ruta, self.semana, self.rango = catalogo, ruta, semana, rango
        self.contexto = Contexto(archivado=True)
        self.repertorio = cargar_repertorio({'esquema':1,'entradas':[{'rol':r,'heroe_id':resolver(catalogo,n),'dominio':None} for r,ns in REPERTORIO.items() for n in ns]},catalogo=catalogo)

    def nombres(self, ids):
        return ', '.join(self.catalogo.por_id(i).nombre for i in ids) or 'ninguno registrado'

    def estado(self):
        c=self.contexto
        return f'Posición {c.rol}. Fase declarada: {c.fase or "desconocida"}. Aliados: {self.nombres(c.aliados)}. Enemigos: {self.nombres(c.enemigos)}. Vetados: {self.nombres(c.vetados)}. Candidatos: {self.nombres(c.candidatos)}.' + ''.join(f' {self.nombres((h,))}: posición {r} declarada.' for h,r in c.roles_declarados)

    def responder(self, texto):
        t=normalizar(texto).strip(' .?!¿¡')
        if t in ('reiniciar','nuevo escenario'):
            self.contexto=Contexto(archivado=True); return 'Escenario reiniciado. '+self.estado()
        if t in ('estado','contexto','que sabes'):
            return self.estado()
        if t in ('mi repertorio','que heroes juego'):
            return 'Tu repertorio para esta posición: '+self.nombres(tuple(e.heroe_id for e in self.repertorio.entradas if e.rol==self.contexto.rol))+'. Dominio no cuantificado.'
        if t in ('analizar','analiza','que me conviene','que me recomiendas') or re.match(r'^(?:compara|comparar|que me conviene mas)[ :]+',t):
            c=self.contexto
            m=re.match(r'^(?:compara|comparar|que me conviene mas)[ :]+(.+)$',t)
            if m:
                ns=re.split(r'\s+(?:o|y|contra)\s+|\s*,\s*',m[1]); c=actualizar(c,'Candidatos: '+','.join(ns),self.catalogo)
            if not c.candidatos: return 'Indica candidatos disponibles para el estudio, por ejemplo: Compara Puck o QoP.'
            r=analizar(c,catalogo=self.catalogo,repertorio=self.repertorio,ruta=self.ruta,semana=self.semana,rango=self.rango)
            self.contexto=c
            lineas=['Estudio offline. Rango, posición estadística y vigencia no certificados.']
            for f in r['filas']:
                lineas.append(f"{f['nombre']}: {f['suficientes']} de {f['conocidas']} relaciones con muestra suficiente." + (f" Media descriptiva: {100*f['media']:.2f} por ciento. No es una probabilidad de ganar." if f['media'] is not None else ' Información insuficiente.'))
            return '\n'.join(lineas+['No se emite una recomendación competitiva.'])
        # Añadir un héroe sin borrar los registrados; los comandos con dos puntos reemplazan la lista.
        m=re.fullmatch(r'(mi aliado|mi enemigo|vetaron a)\s+(.+)',t)
        if m:
            campo={'mi aliado':'aliados','mi enemigo':'enemigos','vetaron a':'vetados'}[m[1]]
            h=resolver(self.catalogo,m[2]); c=self.contexto
            ids=getattr(c,campo)
            if h in ids: return self.estado()
            nuevo=replace(c,**{campo:ids+(h,), 'candidatos':tuple(i for i in c.candidatos if i!=h)})
            self.contexto=validar(nuevo,self.catalogo)
        else:
            self.contexto=actualizar(self.contexto,texto,self.catalogo)
        return self.estado()
