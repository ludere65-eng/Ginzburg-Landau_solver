"""
Paquete `tdgl_solver`: Simulación y análisis de vórtices en superconductores
mediante ecuaciones dependientes del tiempo de Ginzburg-Landau (2D y 3D).
"""

from .runner import TDGLRunner
from .io_handler import TDGLDataLoader

__version__ = "0.1.0"
__all__ = ["TDGLRunner", "TDGLDataLoader"]