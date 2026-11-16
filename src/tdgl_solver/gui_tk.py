"""
Interfaz de escritorio nativa usando Tkinter para visualización múltiple
y animación de resultados TDGL respecto al campo magnético H.
"""

import math
from pathlib import Path
from typing import Dict, List
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tdgl_solver.io_handler import TDGLDataLoader


# Mapeo de nombres amigables a rutas reales en disco
RUTAS_MODELOS: Dict[str, str] = {
    "Modularizado": "output_modular",
    "2D_2bandas sin modularizar": "Codigo2/output",
    "3D_1banda sin modularizar": "Codigo3/output",
}

# Etiquetas descriptivas de las variables físicas
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
    """Aplicación principal de Tkinter para análisis visual y animación TDGL."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("TDGL Solver — Visualizador de Escritorio")
        self.root.geometry("1120x720")

        self.loader = None
        self.campos: List[str] = []
        self.vars_disponibles: List[str] = []
        self.datos_actuales: Dict[str, np.ndarray] = {}
        self.animando: bool = False
        self.after_id = None

        self.crear_widgets()
        # Cargar automáticamente el primer modelo disponible al abrir
        self.cargar_modelo_seleccionado()

    def crear_widgets(self) -> None:
        """Construye el panel de control lateral y el lienzo multi-gráfica."""
        frame_ctrl = ttk.Frame(self.root, padding=12, width=270)
        frame_ctrl.pack(side=tk.LEFT, fill=tk.Y)
        frame_ctrl.pack_propagate(False)

        # 1. Selección de fuente de datos
        ttk.Label(
            frame_ctrl, text="1. Conjunto de Simulación:", font=("Sans", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.cb_modelo = ttk.Combobox(
            frame_ctrl, values=list(RUTAS_MODELOS.keys()), state="readonly"
        )
        self.cb_modelo.current(0)
        self.cb_modelo.pack(fill=tk.X, pady=(0, 12))
        self.cb_modelo.bind("<<ComboboxSelected>>", self.cargar_modelo_seleccionado)

        # 2. Selección múltiple de variables
        ttk.Label(
            frame_ctrl, text="2. Variables (Multi-selección):", font=("Sans", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.listbox_vars = tk.Listbox(
            frame_ctrl,
            selectmode=tk.MULTIPLE,
            height=7,
            exportselection=False,
        )
        self.listbox_vars.pack(fill=tk.X, pady=(0, 10))
        self.listbox_vars.bind("<<ListboxSelect>>", self.al_cambiar_variables)

        # Paleta de colores y escala fija
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
            text="Fijar escala (para animación)",
            variable=self.var_fijar_escala,
            command=self.dibujar_cuadricula,
        ).pack(anchor=tk.W, pady=(0, 12))

        # 3. Corte transversal Z (solo 3D)
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

        # 4. Control de Campo Magnético H y Animación
        ttk.Label(
            frame_ctrl, text="4. Campo Magnético (H):", font=("Sans", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))

        self.cb_campo = ttk.Combobox(frame_ctrl, state="readonly")
        self.cb_campo.pack(fill=tk.X, pady=(0, 8))
        self.cb_campo.bind("<<ComboboxSelected>>", self.al_cambiar_campo)

        ttk.Label(frame_ctrl, text="Velocidad animación (ms/cuadro):").pack(anchor=tk.W)
        self.slider_vel = tk.Scale(
            frame_ctrl, from_=80, to=1000, resolution=20, orient=tk.HORIZONTAL
        )
        self.slider_vel.set(300)
        self.slider_vel.pack(fill=tk.X, pady=(0, 8))

        self.btn_animar = ttk.Button(
            frame_ctrl, text="▶ Iniciar Animación en H", command=self.alternar_animacion
        )
        self.btn_animar.pack(fill=tk.X, pady=4)

        # Área principal de gráficas Matplotlib
        self.frame_plot = ttk.Frame(self.root)
        self.frame_plot.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = plt.Figure(figsize=(8.0, 6.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _resolver_ruta(self, ruta_rel: str) -> Path:
        """Busca el directorio relativo desde CWD o desde la raíz del proyecto."""
        p = Path(ruta_rel)
        if p.exists():
            return p
        p_alt = Path(__file__).resolve().parents[2] / ruta_rel
        return p_alt

    def cargar_modelo_seleccionado(self, event=None) -> None:
        """Carga el conjunto de simulación elegido en el menú desplegable."""
        self.detener_animacion()
        opcion = self.cb_modelo.get()
        ruta_real = RUTAS_MODELOS[opcion]
        ruta_path = self._resolver_ruta(ruta_real)

        try:
            self.loader = TDGLDataLoader(str(ruta_path))
            self.campos = self.loader.listar_campos_disponibles()
        except FileNotFoundError:
            self.fig.clear()
            self.canvas.draw()
            messagebox.showwarning(
                "Directorio no encontrado",
                f"No se encontró `{ruta_real}` para {opcion}.",
            )
            return

        if not self.campos:
            messagebox.showinfo("Sin datos", f"La carpeta `{ruta_real}` está vacía.")
            return

        self.cb_campo["values"] = self.campos
        self.cb_campo.current(0)

        # Cargar primer paso para poblar la lista de variables
        self.datos_actuales = self.loader.cargar_paso_campo(self.campos[0])
        self.vars_disponibles = list(self.datos_actuales.keys())

        self.listbox_vars.delete(0, tk.END)
        for v in self.vars_disponibles:
            self.listbox_vars.insert(tk.END, NOMBRES_VARIABLES.get(v, v))

        # Seleccionar las primeras 2 variables por defecto
        for idx in range(min(2, len(self.vars_disponibles))):
            self.listbox_vars.selection_set(idx)

        self.configurar_slider_z()
        self.dibujar_cuadricula()

    def configurar_slider_z(self) -> None:
        """Habilita o deshabilita el deslizador Z según si los datos son 3D."""
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
        """Carga las matrices del campo magnético H elegido."""
        if not self.loader or not self.cb_campo.get():
            return
        self.datos_actuales = self.loader.cargar_paso_campo(self.cb_campo.get())
        self.dibujar_cuadricula()

    def al_cambiar_variables(self, event=None) -> None:
        """Redibuja la cuadrícula al marcar o desmarcar variables."""
        self.dibujar_cuadricula()

    def al_mover_slider_z(self, val) -> None:
        """Actualiza el corte Z y redibuja."""
        self.lbl_z.config(text=f"3. Corte Transversal Z: {val}")
        self.dibujar_cuadricula()

    def dibujar_cuadricula(self) -> None:
        """Renderiza todas las variables seleccionadas en una cuadrícula compacta."""
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
                vista,
                cmap=cmap_name,
                origin="lower",
                vmin=vmin,
                vmax=vmax,
                aspect="equal",
            )
            cbar = self.fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.ax.tick_params(labelsize=7)

            titulo = NOMBRES_VARIABLES.get(var_key, var_key)
            ax.set_title(f"{titulo}\n({subtitulo})", fontsize=8.5, fontweight="bold")
            ax.tick_params(labelsize=7)

        self.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def alternar_animacion(self) -> None:
        """Inicia o detiene la reproducción secuencial sobre los valores de H."""
        if self.animando:
            self.detener_animacion()
        else:
            if not self.campos:
                return
            self.animando = True
            self.btn_animar.config(text="⏹ Detener Animación")
            self._paso_animacion()

    def detener_animacion(self) -> None:
        """Cancela el temporizador de animación activo."""
        self.animando = False
        self.btn_animar.config(text="▶ Iniciar Animación en H")
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _paso_animacion(self) -> None:
        """Avanza un paso en el campo magnético H y programa el siguiente cuadro."""
        if not self.animando:
            return

        idx_actual = self.cb_campo.current()
        siguiente_idx = (idx_actual + 1) % len(self.campos)
        self.cb_campo.current(siguiente_idx)
        self.al_cambiar_campo()

        retardo_ms = int(self.slider_vel.get())
        self.after_id = self.root.after(retardo_ms, self._paso_animacion)


def main() -> None:
    root = tk.Tk()
    app = TDGLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()