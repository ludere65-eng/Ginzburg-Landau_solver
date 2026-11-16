"""
Módulo de entrada/salida (I/O) para cargar matrices .mat generadas por el motor TDGL
(compatible con formato binario MATLAB y formato texto ASCII de GNU Octave).
"""

from pathlib import Path
from typing import Dict, List
import numpy as np
from scipy.io import loadmat


def _leer_octave_texto(ruta: Path) -> np.ndarray:
    """Parsea un archivo guardado en formato texto ASCII por defecto de GNU Octave."""
    valores = []
    shape = []
    data_start_idx = 0
    
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()
        
    # 1. Encontrar dónde empiezan los datos y extraer las dimensiones
    for i, linea in enumerate(lineas):
        s = linea.strip()
        if s.startswith("# ndims:"):
            # En matrices 3D, Octave pone las dimensiones en la siguiente línea
            dims_line = lineas[i+1].strip()
            shape = [int(x) for x in dims_line.split()]
            data_start_idx = i + 2
            break
        elif s.startswith("# rows:"):
            shape.append(int(s.split(":")[1]))
        elif s.startswith("# columns:"):
            shape.append(int(s.split(":")[1]))
            data_start_idx = i + 1
            break
            
    # 2. Leer únicamente los valores numéricos
    for linea in lineas[data_start_idx:]:
        s = linea.strip()
        if not s or s.startswith("#"):
            continue
        for token in s.split():
            if token.startswith("(") and token.endswith(")"):
                # Formato de números complejos en Octave: (real,imag)
                re_str, im_str = token[1:-1].split(",")
                valores.append(complex(float(re_str), float(im_str)))
            else:
                # Números reales
                valores.append(float(token))
                
    arr = np.array(valores)
    if shape:
        # Octave guarda en orden Fortran (columna-mayor)
        arr = arr.reshape(shape, order="F")
    return arr


class TDGLDataLoader:
    """Cargador estructurado de resultados físicos en formato `.mat` o Octave ASCII."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = Path(output_dir).resolve()
        if not self.output_dir.exists():
            raise FileNotFoundError(f"No se encontró el directorio: {self.output_dir}")

    def listar_campos_disponibles(self) -> List[str]:
        psi_dir = self.output_dir / "psi"
        if not psi_dir.exists():
            return []
        carpetas = [d.name for d in psi_dir.iterdir() if d.is_dir()]
        return sorted(carpetas, key=lambda x: float(x))

    def cargar_paso_campo(self, h_str: str) -> Dict[str, np.ndarray]:
        mapa_archivos = {
            "d": ("psi", "d.mat"),
            "d4": ("psi", "d4.mat"),
            "B": ("psi", "B.mat"),
            "d2": ("psi", "d2.mat"),
            "hz": ("field", "hz.mat"),
            "phase": ("phase", "phase.mat"),
            "aJx": ("currentsx", "aJx.mat"),
            "aJy": ("currentsy", "aJy.mat"),
        }

        datos: Dict[str, np.ndarray] = {}
        for var_name, (subcarpeta, filename) in mapa_archivos.items():
            ruta = self.output_dir / subcarpeta / h_str / filename
            if ruta.exists():
                try:
                    mat = loadmat(str(ruta))
                    if var_name in mat:
                        datos[var_name] = np.asarray(mat[var_name])
                except ValueError:
                    # Fallback automático para formato ASCII por defecto de GNU Octave
                    datos[var_name] = _leer_octave_texto(ruta)

        return datos