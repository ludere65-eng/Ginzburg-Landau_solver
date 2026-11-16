"""
Interfaz de escritorio nativa usando Tkinter para cargar y visualizar resultados TDGL.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tdgl_solver.io_handler import TDGLDataLoader


class TDGLApp:
    """Aplicación principal de Tkinter para la visualización de datos TDGL."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("TDGL Solver - Visualizador de Escritorio")
        self.root.geometry("850x620")

        self.loader = None
        self.campos = []
        self.datos_actuales = {}

        self.crear_widgets()

    def crear_widgets(self) -> None:
        """Construye los paneles de control y el área de trazado."""
        frame_ctrl = ttk.Frame(self.root, padding=10)
        frame_ctrl.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Button(
            frame_ctrl, text="Cargar Directorio Output", command=self.cargar_directorio
        ).pack(pady=10, fill=tk.X)

        ttk.Label(frame_ctrl, text="Seleccionar Campo H:").pack(pady=(10, 0))
        self.cb_campo = ttk.Combobox(frame_ctrl, state="readonly")
        self.cb_campo.pack(pady=5, fill=tk.X)
        self.cb_campo.bind("<<ComboboxSelected>>", self.actualizar_datos)

        ttk.Label(frame_ctrl, text="Variable Física:").pack(pady=(10, 0))
        self.cb_var = ttk.Combobox(frame_ctrl, state="readonly")
        self.cb_var.pack(pady=5, fill=tk.X)
        self.cb_var.bind("<<ComboboxSelected>>", self.al_cambiar_variable)

        # Control deslizante para corte transversal Z en volúmenes 3D
        self.lbl_z = ttk.Label(frame_ctrl, text="Corte Z (Solo 3D): 0")
        self.lbl_z.pack(pady=(15, 0))
        self.slider_z = tk.Scale(
            frame_ctrl,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            command=self.al_mover_slider_z,
            state=tk.DISABLED,
        )
        self.slider_z.pack(pady=5, fill=tk.X)

        # Área de visualización Matplotlib
        self.frame_plot = ttk.Frame(self.root)
        self.frame_plot.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = plt.Figure(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def cargar_directorio(self) -> None:
        """Abre un diálogo para seleccionar el directorio de resultados."""
        dir_path = filedialog.askdirectory(
            title="Seleccionar carpeta de resultados (ej. output_modular)"
        )
        if dir_path:
            try:
                self.loader = TDGLDataLoader(dir_path)
                self.campos = self.loader.listar_campos_disponibles()
                self.cb_campo["values"] = self.campos
                if self.campos:
                    self.cb_campo.current(0)
                    self.actualizar_datos()
            except Exception as e:
                messagebox.showerror("Error de Carga", str(e))

    def actualizar_datos(self, event=None) -> None:
        """Carga las matrices correspondientes al campo magnético seleccionado."""
        if not self.loader or not self.cb_campo.get():
            return

        h_str = self.cb_campo.get()
        self.datos_actuales = self.loader.cargar_paso_campo(h_str)

        vars_disp = list(self.datos_actuales.keys())
        self.cb_var["values"] = vars_disp
        if vars_disp:
            self.cb_var.current(0)
            self.al_cambiar_variable()

    def al_cambiar_variable(self, event=None) -> None:
        """Ajusta el slider Z si la matriz es 3D y actualiza la gráfica."""
        var_name = self.cb_var.get()
        if not var_name or var_name not in self.datos_actuales:
            return

        matriz = self.datos_actuales[var_name]
        if matriz.ndim == 3:
            max_z = matriz.shape[2] - 1
            self.slider_z.config(state=tk.NORMAL, from_=0, to=max_z)
            self.slider_z.set(max_z // 2)
        else:
            self.slider_z.set(0)
            self.slider_z.config(state=tk.DISABLED)
            self.lbl_z.config(text="Corte Z: N/A (2D)")

        self.dibujar_grafica()

    def al_mover_slider_z(self, val) -> None:
        """Actualiza la etiqueta de capa Z y redibuja al mover el slider."""
        self.lbl_z.config(text=f"Corte Z (Solo 3D): {val}")
        self.dibujar_grafica()

    def dibujar_grafica(self) -> None:
        """Renderiza la matriz en el canvas de Matplotlib limpiando la figura previa."""
        var_name = self.cb_var.get()
        if not var_name or var_name not in self.datos_actuales:
            return

        matriz = self.datos_actuales[var_name]
        if matriz.ndim == 3:
            z_idx = int(self.slider_z.get())
            vista = matriz[:, :, z_idx]
            titulo = f"{var_name} (H = {self.cb_campo.get()}, Z = {z_idx})"
        else:
            vista = matriz
            titulo = f"{var_name} (H = {self.cb_campo.get()})"

        # Limpiar toda la figura evita el KeyError con el colorbar en Matplotlib moderno
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        im = ax.imshow(vista, cmap="viridis", origin="lower")
        self.fig.colorbar(im, ax=ax)
        ax.set_title(titulo)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        self.canvas.draw()


def main():
    root = tk.Tk()
    app = TDGLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()