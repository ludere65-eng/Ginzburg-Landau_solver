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
        self.root.geometry("800x600")
        
        self.loader = None
        self.campos = []
        self.datos_actuales = {}
        
        self.crear_widgets()
        
    def crear_widgets(self) -> None:
        """Construye los paneles de control y el área de trazado."""
        # Panel lateral
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
        self.cb_var.bind("<<ComboboxSelected>>", self.dibujar_grafica)
        
        # Área de visualización Matplotlib
        self.frame_plot = ttk.Frame(self.root)
        self.frame_plot.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.color_bar = None
        
    def cargar_directorio(self) -> None:
        """Abre un diálogo para seleccionar el directorio de resultados."""
        dir_path = filedialog.askdirectory(title="Seleccionar carpeta de resultados (ej. output_modular)")
        if dir_path:
            try:
                self.loader = TDGLDataLoader(dir_path)
                self.campos = self.loader.listar_campos_disponibles()
                self.cb_campo['values'] = self.campos
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
        self.cb_var['values'] = vars_disp
        if vars_disp:
            self.cb_var.current(0)
            self.dibujar_grafica()
            
    def dibujar_grafica(self, event=None) -> None:
        """Renderiza la matriz en el canvas de Matplotlib."""
        var_name = self.cb_var.get()
        if not var_name or var_name not in self.datos_actuales: 
            return
            
        matriz = self.datos_actuales[var_name]
        # Toma la rebanada central si es un volumen 3D
        vista = matriz[:, :, matriz.shape[2]//2] if matriz.ndim == 3 else matriz
        
        self.ax.clear()
        if self.color_bar:
            self.color_bar.remove()
            
        im = self.ax.imshow(vista, cmap='viridis', origin='lower')
        self.color_bar = self.fig.colorbar(im, ax=self.ax)
        self.ax.set_title(f"{var_name} (H = {self.cb_campo.get()})")
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = TDGLApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()