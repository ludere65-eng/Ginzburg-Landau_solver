"""
Módulo de entrada/salida (I/O) para cargar matrices .mat generadas por el motor TDGL.
"""

from pathlib import Path
from typing import Dict, List
import numpy as np
from scipy.io import loadmat


class TDGLDataLoader:
    """Cargador estructurado de resultados físicos en formato `.mat`.

    Attributes:
        output_dir (Path): Ruta raíz donde se encuentran las subcarpetas
            `psi/`, `field/`, `phase/`, `currentsx/`, etc.
    """

    def __init__(self, output_dir: str) -> None:
        """Inicializa el cargador verificando que exista el directorio de salida.

        Args:
            output_dir (str): Ruta al directorio de resultados (ej. `'output_modular'`).

        Raises:
            FileNotFoundError: Si la ruta especificada no existe.
        """
        self.output_dir = Path(output_dir).resolve()
        if not self.output_dir.exists():
            raise FileNotFoundError(f"No se encontró el directorio: {self.output_dir}")

    def listar_campos_disponibles(self) -> List[str]:
        """Lista los valores de campo magnético H disponibles ordenados numéricamente.

        Returns:
            List[str]: Nombres de las subcarpetas de campo H (ej. `['0', '0.1', '0.2']`).
        """
        psi_dir = self.output_dir / "psi"
        if not psi_dir.exists():
            return []
        carpetas = [d.name for d in psi_dir.iterdir() if d.is_dir()]
        return sorted(carpetas, key=lambda x: float(x))

    def cargar_paso_campo(self, h_str: str) -> Dict[str, np.ndarray]:
        """Carga todas las matrices físicas disponibles para un valor de campo H.

        Args:
            h_str (str): Identificador del campo magnético (ej. `'0.1'`).

        Returns:
            Dict[str, np.ndarray]: Diccionario cuyas claves son los nombres de las
                variables (`'d'`, `'d4'`, `'B'`, `'hz'`, `'phase'`, `'aJx'`, `'aJy'`)
                y sus valores son los arreglos de NumPy correspondientes.
        """
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
                mat = loadmat(str(ruta))
                if var_name in mat:
                    datos[var_name] = np.asarray(mat[var_name])

        return datos