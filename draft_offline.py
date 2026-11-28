"""Herramienta local para estudiar escenarios archivados. Sin red ni captura."""
import json
import sys
from pathlib import Path
from coach.datos.catalogo_heroes import CatalogoHeroes, importar_heroes
from coach.draft.repertorio import cargar_repertorio
from coach.draft.sesion_offline import analizar_sesion
from coach.draft.chat_offline import ChatOffline


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
        win=tk.Toplevel(root); win.title('DotaCoach | ENIGMA - Estudio offline'); win.geometry('760x540'); win.configure(bg='#171b22')
        ttk.Label(win,text='ENIGMA | Asistente de estudio de Dota 2').pack(anchor='w',padx=12,pady=8)
        ttk.Label(win,text='Solo escenarios archivados. Sin micrófono ni IA remota todavía.').pack(anchor='w',padx=12)
        historial=tk.Text(win,wrap='word',bg='#171b22',fg='#e5e7eb',insertbackground='white'); historial.pack(fill='both',expand=True,padx=12,pady=8)
        historial.insert('end','Coach: Soy tu asistente de estudio. Prueba Soy mid, Aliados: Lion, Axe, Mi Axe juega de 5, o Compara Puck o QoP.\n'); historial.config(state='disabled')
        entrada=ttk.Entry(win); entrada.pack(fill='x',padx=12,pady=4)
        def enviar(event=None):
            texto=entrada.get().strip()
            if not texto: return
            entrada.delete(0,'end')
            try: respuesta=chat.responder(texto)
            except Exception as exc: respuesta='No pude procesar esa entrada: '+str(exc)
            historial.config(state='normal'); historial.insert('end','\nTú: '+texto+'\nCoach: '+respuesta+'\n'); historial.config(state='disabled'); historial.see('end')
        entrada.bind('<Return>',enviar); ttk.Button(win,text='Enviar',command=enviar).pack(pady=5); entrada.focus_set()
    ttk.Button(frame,text='Abrir chat de estudio offline',command=abrir_chat).pack(anchor='w')
    root.mainloop()

if __name__=='__main__':
    if sys.argv[1:]==['--self-test']:
        assert len(catalogo_local().heroes)>1
    else: main()
