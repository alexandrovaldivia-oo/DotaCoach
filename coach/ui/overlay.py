"""Overlay minimo con tkinter (ventana sin bordes, siempre arriba).
La interfaz completa (paneles, historial, perfiles) vendra en la etapa 4;
el resto del programa solo usa mostrar() y estado(), asi que se podra reemplazar."""
import tkinter as tk
from tkinter import messagebox
import queue
import threading

from ..persona import PERSONAS

FONDO = "#121614"
BARRA = "#1b241e"
VERDE = "#4caf50"
TEXTO = "#e8f5e9"


class Overlay:
    def __init__(self, cfg, al_guardar, al_probar_voz, al_practica, al_detener):
        self.cfg = cfg
        self.al_guardar = al_guardar
        self.al_probar_voz = al_probar_voz
        self.al_practica = al_practica
        self.al_detener = al_detener
        self._mensajes = queue.Queue(maxsize=16)
        self._estado_lock = threading.Lock()
        self._estado_pendiente = None
        self._vigente = None
        self.root = tk.Tk()
        self._dx = 0
        self._dy = 0
        self._construir()
        self.root.after(100, self._actualizar)

    def _construir(self):
        r = self.root
        r.title("Dota 2 AI Coach")
        r.geometry("460x370+50+120")
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.93)
        r.configure(bg=FONDO, highlightbackground=VERDE, highlightthickness=2)

        barra = tk.Frame(r, bg=BARRA)
        barra.pack(fill="x", padx=4, pady=4)
        barra.bind("<Button-1>", self._iniciar_arrastre)
        barra.bind("<B1-Motion>", self._arrastrar)
        self.lbl_estado = tk.Label(barra, text="Esperando partida de Dota 2...", bg=BARRA, fg=TEXTO,
                                   font=("Segoe UI", 9, "bold"))
        self.lbl_estado.pack(side="left", padx=6)
        self.lbl_estado.bind("<Button-1>", self._iniciar_arrastre)
        self.lbl_estado.bind("<B1-Motion>", self._arrastrar)
        tk.Button(barra, text="X", command=r.destroy, bg=BARRA, fg=TEXTO, bd=0).pack(side="right", padx=4)

        self.lbl_mensaje = tk.Label(r, text="Listo.", bg=FONDO, fg="#a5d6a7", wraplength=430,
                                    justify="left", font=("Segoe UI", 11), height=4, anchor="nw")
        self.lbl_mensaje.pack(fill="x", padx=10, pady=6)

        panel = tk.Frame(r, bg=FONDO)
        panel.pack(fill="x", padx=10)
        tk.Label(panel, text="API key de Gemini", bg=FONDO, fg=TEXTO).grid(row=0, column=0, sticky="w")
        self.entry_key = tk.Entry(panel, show="*", width=34)
        self.entry_key.insert(0, self.cfg.get("api_key", ""))
        self.entry_key.grid(row=0, column=1, padx=6, pady=2)

        tk.Label(panel, text="Personalidad", bg=FONDO, fg=TEXTO).grid(row=1, column=0, sticky="w")
        self.var_persona = tk.StringVar(value=self.cfg.get("persona", "profesional"))
        tk.OptionMenu(panel, self.var_persona, *PERSONAS.keys()).grid(row=1, column=1, sticky="w", padx=6)

        self.var_voz = tk.BooleanVar(value=self.cfg.get("voz", True))
        self.var_comp = tk.BooleanVar(value=self.cfg.get("modo_competitivo", False))
        tk.Checkbutton(panel, text="Voz activada", variable=self.var_voz, bg=FONDO, fg=TEXTO,
                       selectcolor=BARRA, activebackground=FONDO).grid(row=2, column=0, columnspan=2, sticky="w")
        tk.Checkbutton(panel, text="Modo competitivo (sin consejos)", variable=self.var_comp, bg=FONDO,
                       fg=TEXTO, selectcolor=BARRA, activebackground=FONDO).grid(row=3, column=0, columnspan=2, sticky="w")

        botones = tk.Frame(r, bg=FONDO)
        botones.pack(fill="x", padx=10, pady=8)
        tk.Button(botones, text="Guardar", command=self._guardar, bg=VERDE, fg="white", bd=0,
                  padx=10).pack(side="left")
        tk.Button(botones, text="Probar voz", command=self.al_probar_voz, bg=BARRA, fg=TEXTO, bd=0,
                  padx=10).pack(side="left", padx=8)

        practicas = tk.Frame(r, bg=FONDO)
        practicas.pack(fill="x", padx=10, pady=4)
        tk.Button(practicas, text="Habilitar práctica actual", command=self._practica).pack(side="left")
        tk.Button(practicas, text="Detener consejos", command=self._detener).pack(side="left", padx=8)

    def _practica(self):
        if messagebox.askyesno("Solo práctica", "¿Confirmas que estás en una partida de práctica y no competitiva?", parent=self.root):
            self.mostrar("Práctica habilitada." if self.al_practica() else "No hay partida activa válida o el modo competitivo está activado.")

    def _detener(self):
        self.al_detener()
        self.mostrar("Consejos desactivados.")

    def _guardar(self):
        self.cfg["api_key"] = self.entry_key.get().strip()
        self.cfg["persona"] = self.var_persona.get()
        self.cfg["voz"] = self.var_voz.get()
        self.cfg["modo_competitivo"] = self.var_comp.get()
        self.al_guardar()
        self.mostrar("Configuracion guardada.")

    def _iniciar_arrastre(self, evento):
        self._dx, self._dy = evento.x, evento.y

    def _arrastrar(self, evento):
        x = self.root.winfo_x() + evento.x - self._dx
        y = self.root.winfo_y() + evento.y - self._dy
        self.root.geometry("+%d+%d" % (x, y))

    # Los productores no llaman a Tk; solo el hilo de la interfaz consume.
    def mostrar(self, texto, vigente=None):
        try:
            self._mensajes.put_nowait((texto, vigente))
        except queue.Full:
            pass

    def estado(self, texto):
        with self._estado_lock:
            self._estado_pendiente = texto

    def _actualizar(self):
        with self._estado_lock:
            texto, self._estado_pendiente = self._estado_pendiente, None
        if texto is not None:
            self.lbl_estado.config(text=texto)
        if self._vigente is not None and not self._vigente():
            self.lbl_mensaje.config(text="")
            self._vigente = None
        for _ in range(16):
            try:
                texto, vigente = self._mensajes.get_nowait()
            except queue.Empty:
                break
            if vigente is None or vigente():
                self.lbl_mensaje.config(text=texto)
                self._vigente = vigente
        self.root.after(100, self._actualizar)

    def ejecutar(self):
        self.root.mainloop()
