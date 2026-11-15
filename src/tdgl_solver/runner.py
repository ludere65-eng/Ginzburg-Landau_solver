"""
Módulo orquestador para ejecutar el motor numérico TDGL en GNU Octave desde Python.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class TDGLRunner:
    """Controlador principal para configurar y ejecutar simulaciones TDGL.

    Esta clase escribe dinámicamente el archivo `config_simulacion.m` dentro
    del motor de Octave empaquetado y lanza la ejecución en modo silencioso.

    Attributes:
        engine_dir (Path): Ruta absoluta al directorio del motor en Octave.
        work_dir (Path): Directorio de trabajo donde se guardarán las salidas.
    """

    def __init__(self, work_dir: Optional[str] = None) -> None:
        """Inicializa el controlador ubicando el motor de Octave empaquetado.

        Args:
            work_dir (Optional[str]): Ruta donde se generará `output_modular/`.
                Si es None, usa el directorio actual de ejecución.
        """
        self.engine_dir = Path(__file__).resolve().parent / "octave_engine"
        self.work_dir = Path(work_dir).resolve() if work_dir else Path.cwd()

    def generar_configuracion(self, params: Dict[str, Any]) -> Path:
        """Escribe el archivo `config_simulacion.m` con los parámetros indicados.

        Args:
            params (Dict[str, Any]): Diccionario con parámetros físicos y numéricos.
                Claves soportadas: `modelo`, `geometria_tau`, `suavizado_bordes`,
                `dx`, `dy`, `dz`, `a`, `b`, `c`, `aa`, `bb`, `cc`, `kappa`,
                `bt`, `T`, `Gap`, `Hi`, `Hf`, `dH`, `eps`, `nMax`, `lMax`,
                `output_dir`.

        Returns:
            Path: Ruta al archivo `config_simulacion.m` generado.
        """
        defaults: Dict[str, Any] = {
            "modelo": "3D_1Banda",
            "geometria_tau": "bloque",
            "suavizado_bordes": "8_vertices",
            "dx": 0.25,
            "dy": 0.25,
            "dz": 0.25,
            "a": 20,
            "b": 20,
            "c": 10,
            "aa": 10,
            "bb": 10,
            "cc": 5,
            "kappa": 1.0,
            "bt": 1.0,
            "T": 0.0,
            "Gap": -0.001,
            "Hi": 0.0,
            "Hf": 2.0,
            "dH": 0.1,
            "eps": 1e-7,
            "nMax": 10000000,
            "lMax": 100,
            "is_restart": False,
            "output_dir": str(self.work_dir / "output_modular"),
            "graficar_en_vivo": False,
            "guardar_campos_extra": False,
        }
        defaults.update(params)

        config_path = self.engine_dir / "config_simulacion.m"
        lines = [
            "function cfg = config_simulacion()",
            "% CONFIG_SIMULACION Generado automáticamente desde Python (tdgl_solver).",
        ]

        for key, val in defaults.items():
            if isinstance(val, bool):
                octave_val = "true" if val else "false"
            elif isinstance(val, str):
                octave_val = f"'{val}'"
            else:
                octave_val = str(val)
            lines.append(f"    cfg.{key} = {octave_val};")

        lines.append("end\n")
        config_path.write_text("\n".join(lines), encoding="utf-8")
        return config_path

    def ejecutar(self, params: Optional[Dict[str, Any]] = None) -> Path:
        """Ejecuta la simulación TDGL llamando a GNU Octave por subproceso.

        Args:
            params (Optional[Dict[str, Any]]): Parámetros opcionales para sobrescribir
                la configuración por defecto antes de correr.

        Returns:
            Path: Ruta al directorio raíz con los resultados `.mat` generados.

        Raises:
            RuntimeError: Si GNU Octave no está instalado o falla durante el cálculo.
        """
        if params:
            self.generar_configuracion(params)

        main_script = self.engine_dir / "main.m"
        cmd = ["octave", "--no-gui", "--quiet", str(main_script)]

        proceso = subprocess.run(
            cmd,
            cwd=str(self.engine_dir),
            text=True,
            capture_output=False,
        )

        if proceso.returncode != 0:
            raise RuntimeError(
                f"La ejecución en Octave falló con código de salida {proceso.returncode}."
            )

        out_dir = (
            Path(params["output_dir"])
            if params and "output_dir" in params
            else self.work_dir / "output_modular"
        )
        return out_dir
