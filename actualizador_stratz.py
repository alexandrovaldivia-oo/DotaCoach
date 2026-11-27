"""Importador local experimental. No solicita token ni realiza llamadas de red."""
import json
import sys
from pathlib import Path
from coach.draft.stratz_cliente import RANGOS
from coach.draft.stratz_descargador import cargar_catalogo
from coach.draft.stratz_almacen import AlmacenStratz
from coach.draft.stratz_validador import validar
from coach.draft.stratz_cliente import extraer


def catalogo():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'coach/datos/recursos/heroes_catalogo.json'


def base_local():
    return Path.home() / '.dotacoach' / 'experimental' / 'stratz.sqlite3'


def importar(ruta, alias, heroe, rango, destino, ruta_catalogo):
    ids = cargar_catalogo(ruta_catalogo)
    # Validar antes de crear o abrir la base de datos.
    grupo = extraer(json.loads(Path(ruta).read_text(encoding='utf-8-sig')), alias)
    semana, filas = validar(grupo, heroe, rango, ids)
    almacen = AlmacenStratz(destino)
    try:
        almacen.guardar(semana, rango, heroe, filas)
    finally:
        almacen.cerrar()
    return semana, len(filas), sorted({f[2] for f in filas})


def main():
    if sys.argv[1:] == ['--self-test']:
        assert len(cargar_catalogo(catalogo())) > 1
        return 0
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk(); root.title('DotaCoach - Importador STRATZ experimental')
    root.geometry('650x380'); root.minsize(600, 380)
    panel = ttk.Frame(root, padding=20); panel.pack(fill='both', expand=True)
    ttk.Label(panel, text='Importacion local de estadisticas', font=('Segoe UI', 15, 'bold')).pack(anchor='w')
    ttk.Label(panel, text='Solo fuera de partida. Sin red. Fuente: https://stratz.com/', wraplength=580).pack(anchor='w', pady=8)
    ruta = tk.StringVar(); alias = tk.StringVar(value='alternativa'); heroe = tk.StringVar(value='39'); rango = tk.StringVar(value='')
    def elegir():
        p = filedialog.askopenfilename(filetypes=[('JSON', '*.json')]);
        if p: ruta.set(p)
    ttk.Button(panel, text='Seleccionar JSON', command=elegir).pack(anchor='w')
    ttk.Entry(panel, textvariable=ruta).pack(fill='x', pady=4)
    for etiqueta, variable in [('Alias de consulta', alias), ('ID del heroe', heroe)]:
        ttk.Label(panel, text=etiqueta).pack(anchor='w'); ttk.Entry(panel, textvariable=variable).pack(fill='x')
    ttk.Label(panel, text='Rango SOLICITADO originalmente (no verificado)').pack(anchor='w')
    ttk.Combobox(panel, textvariable=rango, values=RANGOS, state='readonly').pack(fill='x')
    def ejecutar():
        try:
            if not ruta.get() or not rango.get() or not alias.get().strip(): raise ValueError('Completa archivo, alias y rango.')
            if not messagebox.askyesno('Confirmar procedencia', 'Confirma que el rango elegido coincide con la consulta original y que tienes permiso para guardar esta muestra localmente.'): return
            w, n, etiquetas = importar(ruta.get(), alias.get().strip(), int(heroe.get()), rango.get(), base_local(), catalogo())
            messagebox.showinfo('Importacion experimental', f'Semana: {w}\nRelaciones: {n}\nEtiquetas devueltas: {", ".join(etiquetas)}\nRango no certificado.\nBase: {base_local()}')
        except Exception as exc:
            messagebox.showerror('Importacion rechazada', str(exc))
    ttk.Button(panel, text='Validar e importar', command=ejecutar).pack(anchor='w', pady=12)
    root.mainloop(); return 0


if __name__ == '__main__':
    raise SystemExit(main())
