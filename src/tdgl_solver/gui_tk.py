"""
Interfaz de escritorio nativa en Tkinter con pestañas para Visualización/Animación
y Cálculo de nuevas simulaciones TDGL (en segundo plano con caché de parámetros).
"""

import math
import queue
import threading
from pathlib import Path
from typing import Dict, List, Any
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tdgl_solver.io_handler import TDGLDataLoader
from tdgl_solver.runner import TDGLRunner

RUTAS_BASE: Dict[str, str] = {
    "Modularizado": "output_modular",
    "2D_2bandas sin modularizar": "Codigo2/output",
    "3D_1banda sin modularizar": "Codigo3/output",
}

NOMBRES_VARIABLES: Dict[str, str] = {
    "d": "Densidad Banda 1 (d)",
    "B": "Densidad Banda 2 (B)",
    "d4": "Parámetro Orden 3D (d4)",
    "d2": "Log Orden (d2)",
    "hz": "Campo Magnético (hz)",
    "phase": "Fase (phase)",
    "aJx": "Supercorriente X (aJx)",
    "aJy": "Supercorriente Y (aJy)",
}


class TDGLApp:
    """Aplicación de escritorio con soporte de simulación asíncrona y caché."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("TDGL Solver — Suite de Simulación y Análisis")
        self.root.geometry("1160x750")

        self.runner = TDGLRunner()
        self.rutas_disponibles: Dict[str, str] = {}
        self.loader = None
        self.campos: List[str] = []
        self.vars_disponibles: List[str] = []
        self.datos_actuales: Dict[str, np.ndarray] = {}
        self.animando: bool = False
        self.after_id = None

        self.log_queue: queue.Queue = queue.Queue()
        self.simulando: bool = False

        # Pestañas principales
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_vis = ttk.Frame(self.notebook)
        self.tab_sim = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_vis, text="  📊 Visualizador y Animación  ")
        self.notebook.add(self.tab_sim, text="  ⚙️ Configurar y Simular  ")

        self.crear_tab_visualizador()
        self.crear_tab_simulacion()

        self.actualizar_lista_modelos()
        self.cargar_modelo_seleccionado()

    # -------------------------------------------------------------------------
    # PESTAÑA 1: VISUALIZADOR Y ANIMACIÓN
    # -------------------------------------------------------------------------
    def crear_tab_visualizador(self) -> None:
        frame_ctrl = ttk.Frame(self.tab_vis, padding=12, width=280)
        frame_ctrl.pack(side=tk.LEFT, fill=tk.Y)
        frame_ctrl.pack_propagate(False)

        ttk.Label(
            frame_ctrl, text="1. Conjunto de Simulación:", font=("Sans", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.cb_modelo = ttk.Combobox(frame_ctrl, state="readonly")
        self.cb_modelo.pack(fill=tk.X, pady=(0, 6))
        self.cb_modelo.bind("<<ComboboxSelected>>", self.cargar_modelo_seleccionado)

        ttk.Button(
            frame_ctrl,
            text="🔄 Refrescar Avance / Caché",
            command=self.cargar_modelo_seleccionado,
        ).pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            frame_ctrl, text="2. Variables (Multi-selección):", font=("Sans", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.listbox_vars = tk.Listbox(
            frame_ctrl, selectmode=tk.MULTIPLE, height=7, exportselection=False
        )
        self.listbox_vars.pack(fill=tk.X, pady=(0, 10))
        self.listbox_vars.bind("<<ListboxSelect>>", lambda e: self.dibujar_cuadricula())

        ttk.Label(frame_ctrl, text="Paleta de colores:").pack(anchor=tk.W)
        self.cb_cmap = ttk.Combobox(
            frame_ctrl,
            values=["inferno", "viridis", "plasma", "magma", "twilight", "coolwarm"],
            state="readonly",
        )
        self.cb_cmap.current(0)
        self.cb_cmap.pack(fill=tk.X, pady=(2, 8))
        self.cb_cmap.bind("<<ComboboxSelected>>", lambda e: self.dibujar_cuadricula())

        self.var_fijar_escala = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_ctrl,
            text="Fijar escala de color",
            variable=self.var_fijar_escala,
            command=self.dibujar_cuadricula,
        ).pack(anchor=tk.W, pady=(0, 12))

        self.lbl_z = ttk.Label(
            frame_ctrl, text="3. Corte Transversal Z: N/A", font=("Sans", 10, "bold")
        )
        self.lbl_z.pack(anchor=tk.W, pady=(0, 2))
        self.slider_z = tk.Scale(
            frame_ctrl,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            command=self.al_mover_slider_z,
            state=tk.DISABLED,
        )
        self.slider_z.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            frame_ctrl, text="4. Campo Magnético (H):", font=("Sans", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.cb_campo = ttk.Combobox(frame_ctrl, state="readonly")
        self.cb_campo.pack(fill=tk.X, pady=(0, 8))
        self.cb_campo.bind("<<ComboboxSelected>>", self.al_cambiar_campo)

        ttk.Label(frame_ctrl, text="Velocidad animación (ms):").pack(anchor=tk.W)
        self.slider_vel = tk.Scale(
            frame_ctrl, from_=80, to=1000, resolution=20, orient=tk.HORIZONTAL
        )
        self.slider_vel.set(300)
        self.slider_vel.pack(fill=tk.X, pady=(0, 8))

        self.btn_animar = ttk.Button(
            frame_ctrl, text="▶ Iniciar Animación en H", command=self.alternar_animacion
        )
        self.btn_animar.pack(fill=tk.X, pady=4)

        self.frame_plot = ttk.Frame(self.tab_vis)
        self.frame_plot.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = plt.Figure(figsize=(8.0, 6.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # PESTAÑA 2: CONFIGURACIÓN Y EJECUCIÓN DE SIMULACIONES
    # -------------------------------------------------------------------------
    def crear_tab_simulacion(self) -> None:
        frame_top = ttk.Frame(self.tab_sim)
        frame_top.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            frame_top, text="Seleccionar Modelo a Simular:", font=("Sans", 11, "bold")
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.var_sim_modelo = tk.StringVar(value="2D_2Bandas")
        ttk.Radiobutton(
            frame_top,
            text="2D (2 Bandas acopladas)",
            variable=self.var_sim_modelo,
            value="2D_2Bandas",
            command=self.actualizar_campos_formulario,
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            frame_top,
            text="3D (1 Banda con caja interna)",
            variable=self.var_sim_modelo,
            value="3D_1Banda",
            command=self.actualizar_campos_formulario,
        ).pack(side=tk.LEFT, padx=10)

        # Contenedor de 3 columnas para parámetros
        frame_cols = ttk.Frame(self.tab_sim)
        frame_cols.pack(fill=tk.X, pady=5)

        col1 = ttk.LabelFrame(frame_cols, text="1. Geometría y Malla", padding=10)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        col2 = ttk.LabelFrame(frame_cols, text="2. Física y Bordes", padding=10)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        col3 = ttk.LabelFrame(frame_cols, text="3. Barrido Magnético y Control", padding=10)
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.entries: Dict[str, tk.Variable] = {}

        def agregar_campo(parent, label_txt: str, key: str, default_val: Any):
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label_txt, width=22).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default_val))
            ent = ttk.Entry(row, textvariable=var, width=12)
            ent.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            self.entries[key] = var
            return ent

        # Columna 1: Geometría
        agregar_campo(col1, "Paso dx:", "dx", "0.25")
        agregar_campo(col1, "Paso dy:", "dy", "0.25")
        self.ent_dz = agregar_campo(col1, "Paso dz (3D):", "dz", "0.25")
        agregar_campo(col1, "Caja ext. X (a):", "a", "10.0")
        agregar_campo(col1, "Caja ext. Y (b):", "b", "10.0")
        self.ent_c = agregar_campo(col1, "Caja ext. Z (c, 3D):", "c", "10.0")
        self.ent_aa = agregar_campo(col1, "Caja int. X (aa, 3D):", "aa", "10.0")
        self.ent_bb = agregar_campo(col1, "Caja int. Y (bb, 3D):", "bb", "10.0")
        self.ent_cc = agregar_campo(col1, "Caja int. Z (cc, 3D):", "cc", "5.0")

        # Columna 2: Física
        agregar_campo(col2, "Kappa (κ):", "kappa", "1.0")
        agregar_campo(col2, "Relajación (bt):", "bt", "1.0")
        agregar_campo(col2, "Temperatura (T):", "T", "0.0")
        self.ent_gap = agregar_campo(col2, "Acoplamiento (Gap, 2D):", "Gap", "-0.001")

        row_tau = ttk.Frame(col2)
        row_tau.pack(fill=tk.X, pady=3)
        ttk.Label(row_tau, text="Geometría tau (3D):", width=22).pack(side=tk.LEFT)
        self.var_tau = tk.StringVar(value="bloque")
        self.cb_tau = ttk.Combobox(
            row_tau, textvariable=self.var_tau, values=["bloque", "estricto"], state="readonly"
        )
        self.cb_tau.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        row_suav = ttk.Frame(col2)
        row_suav.pack(fill=tk.X, pady=3)
        ttk.Label(row_suav, text="Suavizado bordes (3D):", width=22).pack(side=tk.LEFT)
        self.var_suav = tk.StringVar(value="8_vertices")
        self.cb_suav = ttk.Combobox(
            row_suav,
            textvariable=self.var_suav,
            values=["8_vertices", "12_aristas", "ambos"],
            state="readonly",
        )
        self.cb_suav.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Columna 3: Barrido de campo H
        agregar_campo(col3, "Campo inicial (Hi):", "Hi", "0.0")
        agregar_campo(col3, "Campo final (Hf):", "Hf", "0.2")
        agregar_campo(col3, "Paso de campo (dH):", "dH", "0.1")
        agregar_campo(col3, "Tolerancia (eps):", "eps", "1e-5")
        agregar_campo(col3, "Iteraciones máx (nMax):", "nMax", "10000000")
        agregar_campo(col3, "Sub-iteraciones (lMax):", "lMax", "100")

        # Botón de ejecución y consola de progreso
        frame_run = ttk.Frame(self.tab_sim)
        frame_run.pack(fill=tk.X, pady=10)

        self.btn_ejecutar = ttk.Button(
            frame_run,
            text="🚀 Ejecutar Simulación (o Cargar si ya existe en Caché)",
            command=self.iniciar_simulacion_hilo,
        )
        self.btn_ejecutar.pack(side=tk.LEFT, padx=(0, 15))

        self.lbl_estado_sim = ttk.Label(
            frame_run, text="Listo para simular.", font=("Sans", 10, "bold")
        )
        self.lbl_estado_sim.pack(side=tk.LEFT)

        ttk.Label(self.tab_sim, text="Consola de progreso en tiempo real (GNU Octave):").pack(
            anchor=tk.W
        )
        self.txt_log = tk.Text(self.tab_sim, height=12, bg="#1e1e1e", fg="#d4d4d4")
        self.txt_log.pack(fill=tk.BOTH, expand=True, pady=4)

        self.actualizar_campos_formulario()

    def actualizar_campos_formulario(self) -> None:
        """Habilita o deshabilita campos exclusivos de 2D o 3D para guiar al usuario."""
        es_3d = self.var_sim_modelo.get() == "3D_1Banda"
        estado_3d = tk.NORMAL if es_3d else tk.DISABLED
        estado_2d = tk.DISABLED if es_3d else tk.NORMAL

        for w in (self.ent_dz, self.ent_c, self.ent_aa, self.ent_bb, self.ent_cc):
            w.config(state=estado_3d)
        self.cb_tau.config(state="readonly" if es_3d else tk.DISABLED)
        self.cb_suav.config(state="readonly" if es_3d else tk.DISABLED)
        self.ent_gap.config(state=estado_2d)

        if es_3d:
            self.entries["a"].set("20.0")
            self.entries["b"].set("20.0")
            self.entries["eps"].set("1e-7")
        else:
            self.entries["a"].set("10.0")
            self.entries["b"].set("10.0")
            self.entries["eps"].set("1e-5")

    def recolectar_parametros(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {"modelo": self.var_sim_modelo.get()}
        for k, var in self.entries.items():
            params[k] = float(var.get()) if k not in ("nMax", "lMax") else int(float(var.get()))
        params["geometria_tau"] = self.var_tau.get()
        params["suavizado_bordes"] = self.var_suav.get()
        return params

    def iniciar_simulacion_hilo(self) -> None:
        if self.simulando:
            messagebox.showinfo("Ocupado", "Ya hay una simulación en curso.")
            return

        try:
            params = self.recolectar_parametros()
        except ValueError as e:
            messagebox.showerror("Error en parámetros", f"Verifica que todos los números sean válidos:\n{e}")
            return

        en_cache, run_dir, _ = self.runner.verificar_cache(params)
        if en_cache:
            messagebox.showinfo(
                "Parámetros ya ejecutados",
                f"Estos parámetros ya fueron ejecutados anteriormente.\n\n"
                f"Se cargarán directamente los resultados desde:\n{run_dir.name}",
            )
            self.seleccionar_y_mostrar_corrida(run_dir)
            return

        # Iniciar ejecución en segundo plano
        self.simulando = True
        self.btn_ejecutar.config(state=tk.DISABLED)
        self.lbl_estado_sim.config(text=f"Calculando en {run_dir.name}...")
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.insert(tk.END, f"Iniciando Octave en carpeta: {run_dir}\n")

        def tarea_background():
            try:
                out_dir, _ = self.runner.ejecutar_con_progreso(
                    params,
                    callback_linea=lambda lin: self.log_queue.put(("LOG", lin)),
                )
                self.log_queue.put(("DONE", str(out_dir)))
            except Exception as exc:
                self.log_queue.put(("ERR", str(exc)))

        threading.Thread(target=tarea_background, daemon=True).start()
        self.root.after(150, self.procesar_cola_logs)

    def procesar_cola_logs(self) -> None:
        while not self.log_queue.empty():
            tipo, msg = self.log_queue.get_nowait()
            if tipo == "LOG":
                self.txt_log.insert(tk.END, msg + "\n")
                self.txt_log.see(tk.END)
                # Si se completó un campo H, refrescar lista por si el usuario quiere ir viendo
                if "completado en" in msg:
                    self.actualizar_lista_modelos()
            elif tipo == "DONE":
                self.simulando = False
                self.btn_ejecutar.config(state=tk.NORMAL)
                self.lbl_estado_sim.config(text="¡Simulación completada!")
                messagebox.showinfo(
                    "Simulación Finalizada",
                    "El cálculo ha concluido exitosamente. Pasando al visualizador.",
                )
                self.seleccionar_y_mostrar_corrida(Path(msg))
                return
            elif tipo == "ERR":
                self.simulando = False
                self.btn_ejecutar.config(state=tk.NORMAL)
                self.lbl_estado_sim.config(text="Error en la simulación.")
                messagebox.showerror("Error en Octave", msg)
                return

        if self.simulando:
            self.root.after(150, self.procesar_cola_logs)

    def seleccionar_y_mostrar_corrida(self, run_dir: Path) -> None:
        self.actualizar_lista_modelos()
        for etiqueta, ruta_str in self.rutas_disponibles.items():
            if Path(ruta_str).resolve() == run_dir.resolve():
                self.cb_modelo.set(etiqueta)
                break
        self.cargar_modelo_seleccionado()
        self.notebook.select(self.tab_vis)

    # -------------------------------------------------------------------------
    # LÓGICA DE CARGA Y GRAFICACIÓN
    # -------------------------------------------------------------------------
    def actualizar_lista_modelos(self) -> None:
        seleccion_previa = self.cb_modelo.get()
        self.rutas_disponibles = dict(RUTAS_BASE)
        self.rutas_disponibles.update(self.runner.listar_simulaciones_cacheadas())
        claves = list(self.rutas_disponibles.keys())
        self.cb_modelo["values"] = claves
        if seleccion_previa in claves:
            self.cb_modelo.set(seleccion_previa)
        elif claves:
            self.cb_modelo.current(0)

    def _resolver_ruta(self, ruta_rel: str) -> Path:
        p = Path(ruta_rel)
        if p.exists():
            return p
        return Path(__file__).resolve().parents[2] / ruta_rel

    def cargar_modelo_seleccionado(self, event=None) -> None:
        self.detener_animacion()
        self.actualizar_lista_modelos()
        opcion = self.cb_modelo.get()
        if not opcion or opcion not in self.rutas_disponibles:
            return

        ruta_path = self._resolver_ruta(self.rutas_disponibles[opcion])
        try:
            self.loader = TDGLDataLoader(str(ruta_path))
            self.campos = self.loader.listar_campos_disponibles()
        except FileNotFoundError:
            self.fig.clear()
            self.canvas.draw()
            return

        if not self.campos:
            return

        self.cb_campo["values"] = self.campos
        self.cb_campo.current(0)

        self.datos_actuales = self.loader.cargar_paso_campo(self.campos[0])
        self.vars_disponibles = list(self.datos_actuales.keys())

        self.listbox_vars.delete(0, tk.END)
        for v in self.vars_disponibles:
            self.listbox_vars.insert(tk.END, NOMBRES_VARIABLES.get(v, v))

        for idx in range(min(2, len(self.vars_disponibles))):
            self.listbox_vars.selection_set(idx)

        self.configurar_slider_z()
        self.dibujar_cuadricula()

    def configurar_slider_z(self) -> None:
        es_3d = any(mat.ndim == 3 for mat in self.datos_actuales.values())
        if es_3d:
            max_z = max(mat.shape[2] for mat in self.datos_actuales.values() if mat.ndim == 3) - 1
            self.slider_z.config(state=tk.NORMAL, from_=0, to=max_z)
            self.slider_z.set(max_z // 2)
            self.lbl_z.config(text=f"3. Corte Transversal Z: {max_z // 2}")
        else:
            self.slider_z.set(0)
            self.slider_z.config(state=tk.DISABLED)
            self.lbl_z.config(text="3. Corte Transversal Z: N/A (2D)")

    def al_cambiar_campo(self, event=None) -> None:
        if not self.loader or not self.cb_campo.get():
            return
        self.datos_actuales = self.loader.cargar_paso_campo(self.cb_campo.get())
        self.dibujar_cuadricula()

    def al_mover_slider_z(self, val) -> None:
        self.lbl_z.config(text=f"3. Corte Transversal Z: {val}")
        self.dibujar_cuadricula()

    def dibujar_cuadricula(self) -> None:
        indices_sel = self.listbox_vars.curselection()
        vars_sel = [self.vars_disponibles[i] for i in indices_sel]

        self.fig.clear()
        if not vars_sel or not self.datos_actuales:
            self.canvas.draw()
            return

        n_plots = len(vars_sel)
        cols = min(3, n_plots)
        rows = math.ceil(n_plots / cols)

        cmap_name = self.cb_cmap.get()
        fijar = self.var_fijar_escala.get()
        h_str = self.cb_campo.get()
        z_idx = int(self.slider_z.get())

        for idx, var_key in enumerate(vars_sel):
            if var_key not in self.datos_actuales:
                continue

            matriz = self.datos_actuales[var_key]
            if matriz.ndim == 3:
                vista = matriz[:, :, z_idx]
                subtitulo = f"H={h_str} | Z={z_idx}"
            else:
                vista = matriz
                subtitulo = f"H={h_str}"

            vmin, vmax = None, None
            if fijar:
                if var_key in ("d4", "B"):
                    vmin, vmax = 0.0, 1.0
                elif var_key == "phase":
                    vmin, vmax = -np.pi, np.pi

            ax = self.fig.add_subplot(rows, cols, idx + 1)
            im = ax.imshow(
                vista, cmap=cmap_name, origin="lower", vmin=vmin, vmax=vmax, aspect="equal"
            )
            cbar = self.fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.ax.tick_params(labelsize=7)

            titulo = NOMBRES_VARIABLES.get(var_key, var_key)
            ax.set_title(f"{titulo}\n({subtitulo})", fontsize=8.5, fontweight="bold")
            ax.tick_params(labelsize=7)

        self.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def alternar_animacion(self) -> None:
        if self.animando:
            self.detener_animacion()
        else:
            if not self.campos:
                return
            self.animando = True
            self.btn_animar.config(text="⏹ Detener Animación")
            self._paso_animacion()

    def detener_animacion(self) -> None:
        self.animando = False
        self.btn_animar.config(text="▶ Iniciar Animación en H")
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _paso_animacion(self) -> None:
        if not self.animando:
            return
        idx_actual = self.cb_campo.current()
        siguiente_idx = (idx_actual + 1) % len(self.campos)
        self.cb_campo.current(siguiente_idx)
        self.al_cambiar_campo()
        self.after_id = self.root.after(int(self.slider_vel.get()), self._paso_animacion)


def main() -> None:
    root = tk.Tk()
    TDGLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()