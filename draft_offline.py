"""Herramienta local para estudiar escenarios archivados. Sin red ni captura."""
import json
import sys
import threading
from pathlib import Path
from coach.datos.catalogo_heroes import CatalogoHeroes, importar_heroes
from coach.draft.repertorio import cargar_repertorio
from coach.draft.sesion_offline import analizar_sesion
from coach.draft.chat_offline import ChatOffline
from coach.draft.lenguaje_natural import proponer, aplicar
from coach.draft.proveedor_interprete import crear_interprete, ErrorInterpretacion
from coach.draft.voz_enigma import AudioWindows, PERSONALIDADES, respuesta_contextual


def catalogo_local():
    p = Path(__file__).resolve().parent / 'coach/datos/recursos/heroes_valve.json'
    return CatalogoHeroes(importar_heroes(json.loads(p.read_text(encoding='utf-8-sig'))))


def analizar_formulario(campos, *, catalogo, ruta):
    def ids(campo):
        return [int(x.strip()) for x in campos[campo].split(',') if x.strip()]
    rol = int(campos['rol'])
    repertorio = cargar_repertorio({'esquema':1,'entradas':[
        {'rol':rol,'heroe_id':i,'dominio':None} for i in ids('repertorio')]}, catalogo=catalogo)
    return analizar_sesion(catalogo=catalogo,repertorio=repertorio,ruta=ruta,
        semana=int(campos['semana']),rango=campos['rango'],rol=rol,
        aliados=ids('aliados'),enemigos=ids('enemigos'),vetados=ids('vetados'),
        disponibles=ids('disponibles'),archivado=campos['archivado'],
        fase_confirmada=campos['fase'],turno_confirmado=campos['turno'],modo=campos['modo'])


def resumen(resultado):
    lineas = ['ESTUDIO OFFLINE. Sin recomendacion competitiva.',
              'Rango y vigencia no certificados.']
    for f in resultado['candidatos']:
        lineas += ['',f['explicacion']]
    if not resultado['candidatos']:
        lineas.append('No hay candidatos en el modo seleccionado.')
    if not resultado['comparacion_descriptiva_disponible']:
        lineas.append('No existe comparacion estadistica completa entre candidatos.')
    return '\n'.join(lineas)


def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    cat = catalogo_local()
    root = tk.Tk(); root.title('DotaCoach | Estudio de draft offline'); root.geometry('900x720')
    frame=ttk.Frame(root,padding=12); frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Escenarios archivados: no utilizar durante partidas').pack(anchor='w')
    db=tk.StringVar(value=str(Path.home()/'.dotacoach/experimental/stratz.sqlite3'))
    ttk.Button(frame,text='Seleccionar SQLite',command=lambda: db.set(filedialog.askopenfilename(filetypes=[('SQLite','*.sqlite3')]) or db.get())).pack(anchor='w')
    ttk.Entry(frame,textvariable=db).pack(fill='x')
    inputs={}
    defaults={'semana':'2968','rango':'CRUSADER_ARCHON','rol':'2','aliados':'','enemigos':'','vetados':'','disponibles':'','repertorio':'','modo':'equilibrado'}
    for k,v in defaults.items():
        row=ttk.Frame(frame); row.pack(fill='x'); ttk.Label(row,text=k,width=18).pack(side='left')
        inputs[k]=tk.StringVar(value=v)
        if k=='modo': ttk.Combobox(row,textvariable=inputs[k],values=['personal','estrategico','equilibrado'],state='readonly').pack(fill='x')
        else: ttk.Entry(row,textvariable=inputs[k]).pack(fill='x')
    ttk.Label(frame,text='Introduce identificadores separados por comas. Vetos vacios = ninguno confirmado.').pack(anchor='w')
    def mostrar_catalogo():
        win=tk.Toplevel(root); win.title('Catalogo de heroes'); t=tk.Text(win,width=48,height=25); t.pack(fill='both',expand=True)
        t.insert('end','\n'.join(f'{h.id}: {h.nombre}' for h in sorted(cat.heroes,key=lambda h:h.nombre.casefold()))); t.config(state='disabled')
    ttk.Button(frame,text='Consultar identificadores de heroes',command=mostrar_catalogo).pack(anchor='w')
    for k,label in [('archivado','Escenario archivado, fuera de partida'),('fase','Fase de ultimo pick confirmada'),('turno','Turno y disponibilidad confirmados manualmente')]:
        inputs[k]=tk.BooleanVar(value=False); ttk.Checkbutton(frame,text=label,variable=inputs[k]).pack(anchor='w')
    out=tk.Text(frame,height=12,wrap='word')
    def run():
        out.delete('1.0','end')
        try: out.insert('end',resumen(analizar_formulario({k:v.get() for k,v in inputs.items()},catalogo=cat,ruta=Path(db.get()))))
        except Exception as exc: messagebox.showerror('Analisis no realizado',str(exc))
    ttk.Button(frame,text='Analizar escenario archivado',command=run).pack(anchor='w'); out.pack(fill='both',expand=True)
    def abrir_chat():
        try:
            chat=ChatOffline(cat,Path(db.get()),int(inputs['semana'].get()),inputs['rango'].get())
        except Exception as exc:
            messagebox.showerror('Chat no disponible',str(exc)); return
        win=tk.Toplevel(root); win.title('DotaCoach | ENIGMA - Estudio offline'); win.geometry('760x620'); win.minsize(480,360); win.configure(bg='#171b22')
        ttk.Label(win,text='ENIGMA | Asistente de estudio de Dota 2').pack(anchor='w',padx=12,pady=8)
        ttk.Label(win,text='Solo escenarios archivados. IA remota opcional; audio local bajo demanda.').pack(anchor='w',padx=12)
        historial=tk.Text(win,wrap='word',bg='#171b22',fg='#e5e7eb',insertbackground='white'); historial.pack(side='top',fill='both',expand=True,padx=12,pady=8)
        historial.insert('end','Coach: Soy tu asistente de estudio. Prueba Soy mid, Aliados: Lion, Axe, Mi Axe juega de 5, o Compara Puck o QoP.\n'); historial.config(state='disabled')
        controles=ttk.Frame(win); controles.pack(side='bottom',fill='x',padx=12,pady=8,before=historial)
        entrada=ttk.Entry(controles); entrada.pack(fill='x',pady=4)
        remoto=tk.BooleanVar(value=False)
        ttk.Checkbutton(controles,text='Permitir IA remota si el chat local no comprende',variable=remoto).pack(anchor='w')
        audio=AudioWindows()
        import queue
        cola_audio=queue.Queue()
        actividad={'id':0,'ocupado':False}
        voz=tk.BooleanVar(value=False); sarcasmo=tk.BooleanVar(value=False)
        personalidad=tk.StringVar(value='Profesional')
        opciones=ttk.Frame(controles); opciones.pack(fill='x')
        ttk.Checkbutton(opciones,text='Leer respuestas',variable=voz).pack(side='left')
        ttk.Checkbutton(opciones,text='Humor',variable=sarcasmo).pack(side='left')
        ttk.Combobox(opciones,textvariable=personalidad,values=PERSONALIDADES,state='readonly',width=21).pack(side='left')
        estado_audio=tk.StringVar(value='Audio inactivo')
        ttk.Label(controles,textvariable=estado_audio).pack(anchor='w')
        def detener():
            actividad['id']+=1; audio.cancelar(); estado_audio.set('Audio detenido')
        def audio_trabajo(tipo,texto=''):
            if actividad['ocupado']:
                detener(); return
            actividad['id']+=1; ident=actividad['id']; ticket=audio.ticket(); actividad['ocupado']=True
            estado_audio.set('Escuchando...' if tipo=='micro' else 'Hablando...')
            def trabajo_audio():
                try:
                    valor=audio.escuchar(ticket) if tipo=='micro' else audio.hablar(texto,ticket)
                    cola_audio.put((ident,tipo,valor,None))
                except Exception as exc: cola_audio.put((ident,tipo,None,str(exc) if isinstance(exc,RuntimeError) else 'Error de audio local.'))
            threading.Thread(target=trabajo_audio,daemon=True).start()
            def revisar_audio():
                try: i,t,v,error=cola_audio.get_nowait()
                except queue.Empty: win.after(100,revisar_audio); return
                actividad['ocupado']=False
                if i!=actividad['id']: return
                estado_audio.set(error or ('Transcripción lista. Revisa y envía.' if t=='micro' else 'Audio inactivo'))
                if not error and t=='micro' and str(entrada.cget('state'))!='disabled':
                    entrada.delete(0,'end'); entrada.insert(0,v); entrada.focus_set()
            win.after(100,revisar_audio)
        fila_audio=ttk.Frame(controles); fila_audio.pack(fill='x')
        ttk.Button(fila_audio,text='Escuchar una frase',command=lambda: audio_trabajo('micro') if str(entrada.cget('state'))!='disabled' else None).pack(side='left')
        ttk.Button(fila_audio,text='Detener audio',command=detener).pack(side='left')
        def cerrar_chat():
            detener(); win.destroy()
        win.protocol('WM_DELETE_WINDOW',cerrar_chat)
        def publicar(texto,respuesta):
            respuesta=respuesta_contextual(respuesta,chat.estado(),personalidad.get(),sarcasmo.get())
            historial.config(state='normal'); historial.insert('end','\nTú: '+texto+'\nCoach: '+respuesta+'\n'); historial.config(state='disabled'); historial.see('end')
            if voz.get(): audio_trabajo('voz',respuesta)
        def enviar(event=None):
            texto=entrada.get().strip()
            if not texto or str(entrada.cget('state'))=='disabled': return
            anterior=chat.contexto
            try: respuesta=chat.responder(texto)
            except ValueError as exc:
                chat.contexto=anterior
                if remoto.get():
                    interpretar(); return
                respuesta='No pude procesar esa entrada. Activa IA remota o usa un comando local.'
            except Exception:
                chat.contexto=anterior
                respuesta='Error local de análisis. Revisa la base y los parámetros.'
            entrada.delete(0,'end')
            publicar(texto,respuesta)
        def interpretar():
            texto=entrada.get().strip()
            if not texto: return
            if not messagebox.askyesno('IA remota', '¿Enviar esta pregunta y el contexto de héroes y roles a tu proveedor de IA? Solo estudio archivado.',parent=win): return
            from coach.config import cargar
            try: proveedor=crear_interprete(cargar())
            except Exception: messagebox.showerror('IA','Proveedor no disponible',parent=win); return
            anterior=chat.contexto
            # Copia independiente para no leer el contexto mutable desde el hilo.
            import copy
            copia=copy.copy(chat)
            import queue
            resultados=queue.Queue()
            boton.config(state='disabled'); entrada.config(state='disabled')
            def trabajo():
                try: resultados.put((proponer(copia,proveedor,texto),None))
                except ErrorInterpretacion as exc: resultados.put((None,str(exc)))
                except ValueError: resultados.put((None,'La IA devolvió una propuesta inválida o incompatible con el contexto. No se aplicó ningún cambio.'))
                except Exception: resultados.put((None,'Error interno del intérprete. No se aplicó ningún cambio.'))
            def revisar():
                try: propuesta,error=resultados.get_nowait()
                except queue.Empty: win.after(100,revisar); return
                boton.config(state='normal'); entrada.config(state='normal')
                if error: messagebox.showerror('IA',error,parent=win); return
                copia.contexto=propuesta[0]
                if not messagebox.askyesno('Confirmar interpretación',copia.estado()+('\nAnalizar escenario.' if propuesta[1] else '')+'\n¿Aplicar?',parent=win): return
                try: respuesta=aplicar(chat,anterior,propuesta)
                except Exception as exc: messagebox.showerror('IA',str(exc),parent=win); return
                entrada.delete(0,'end'); publicar(texto,respuesta)
            threading.Thread(target=trabajo,daemon=True).start(); win.after(100,revisar)
        entrada.bind('<Return>',enviar)
        boton=ttk.Button(controles,text='Enviar',command=enviar); boton.pack(pady=4); entrada.focus_set()
    ttk.Button(frame,text='Abrir chat de estudio offline',command=abrir_chat).pack(anchor='w')
    root.mainloop()

if __name__=='__main__':
    if sys.argv[1:]==['--self-test']:
        assert len(catalogo_local().heroes)>1
    else: main()
