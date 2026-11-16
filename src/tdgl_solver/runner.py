"""
Módulo orquestador para ejecutar el motor numérico TDGL en GNU Octave desde Python,
con sistema de caché por huella digital (SHA-256) y monitoreo en tiempo real.
"""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable, List


class TDGLRunner:
    """Controlador principal para configurar, cachear y ejecutar simulaciones TDGL."""

    def __init__(self, base_runs_dir: Optional[str] = None) -> None:
        self.engine_dir = Path(__file__).resolve().parent / "octave_engine"
        # Ubicar la raíz del proyecto para guardar las corridas en 'runs/'
        self.project_root = Path(__file__).resolve().parents[2]
        if not (self.project_root / "pyproject.toml").exists():
            self.project_root = Path.cwd()

        self.runs_dir = (
            Path(base_runs_dir).resolve()
            if base_runs_dir
            else (self.project_root / "runs")
        )
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def normalizar_parametros(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Completa valores por defecto y filtra según el modelo (2D_2Bandas vs 3D_1Banda)."""
        modelo = params.get("modelo", "3D_1Banda")

        # Parámetros comunes a ambos modelos
        norm: Dict[str, Any] = {
            "modelo": modelo,
            "dx": float(params.get("dx", 0.25)),
            "dy": float(params.get("dy", 0.25)),
            "a": float(params.get("a", 10.0 if modelo == "2D_2Bandas" else 20.0)),
            "b": float(params.get("b", 10.0 if modelo == "2D_2Bandas" else 20.0)),
            "kappa": float(params.get("kappa", 1.0)),
            "bt": float(params.get("bt", 1.0)),
            "T": float(params.get("T", 0.0)),
            "Hi": float(params.get("Hi", 0.0)),
            "Hf": float(params.get("Hf", 2.0)),
            "dH": float(params.get("dH", 0.1)),
            "eps": float(params.get("eps", 1e-5 if modelo == "2D_2Bandas" else 1e-7)),
            "nMax": int(params.get("nMax", 10000000)),
            "lMax": int(params.get("lMax", 100)),
        }

        if modelo == "3D_1Banda":
            norm.update(
                {
                    "dz": float(params.get("dz", 0.25)),
                    "c": float(params.get("c", 10.0)),
                    "aa": float(params.get("aa", 10.0)),
                    "bb": float(params.get("bb", 10.0)),
                    "cc": float(params.get("cc", 5.0)),
                    "geometria_tau": str(params.get("geometria_tau", "bloque")),
                    "suavizado_bordes": str(
                        params.get("suavizado_bordes", "8_vertices")
                    ),
                    # Valores neutros para config_simulacion.m
                    "Gap": -0.001,
                }
            )
        else:
            norm.update(
                {
                    "Gap": float(params.get("Gap", -0.001)),
                    # Valores neutros para 3D en config_simulacion.m
                    "dz": 0.25,
                    "c": 10.0,
                    "aa": 10.0,
                    "bb": 10.0,
                    "cc": 5.0,
                    "geometria_tau": "bloque",
                    "suavizado_bordes": "8_vertices",
                }
            )

        return norm

    def calcular_hash_y_ruta(self, params: Dict[str, Any]) -> Tuple[str, Path, Dict[str, Any]]:
        """Genera un identificador único (SHA-256) basado únicamente en los parámetros activos."""
        norm = self.normalizar_parametros(params)
        modelo = norm["modelo"]

        # Claves que determinan físicamente la simulación para el hash
        claves_hash = ["modelo", "dx", "dy", "a", "b", "kappa", "bt", "T", "Hi", "Hf", "dH", "eps"]
        if modelo == "3D_1Banda":
            claves_hash.extend(["dz", "c", "aa", "bb", "cc", "geometria_tau", "suavizado_bordes"])
        else:
            claves_hash.extend(["Gap"])

        diccionario_hash = {k: norm[k] for k in sorted(claves_hash)}
        cadena_json = json.dumps(diccionario_hash, sort_keys=True)
        run_id = hashlib.sha256(cadena_json.encode("utf-8")).hexdigest()[:10]

        run_dir = self.runs_dir / f"{modelo}_{run_id}"
        return run_id, run_dir, norm

    def _campos_esperados(self, norm: Dict[str, Any]) -> int:
        """Calcula cuántos pasos de campo H debe generar la simulación."""
        pasos = int(round((norm["Hf"] - norm["Hi"]) / norm["dH"])) + 1
        return max(1, pasos)

    def verificar_cache(self, params: Dict[str, Any]) -> Tuple[bool, Path, Dict[str, Any]]:
        """Verifica si una simulación con exactamente los mismos parámetros ya fue completada.

        Returns:
            Tuple[bool, Path, Dict[str, Any]]:
                - True si ya existe y está completa, False en caso contrario.
                - Ruta al directorio de resultados.
                - Diccionario de parámetros normalizados.
        """
        _, run_dir, norm = self.calcular_hash_y_ruta(params)
        psi_dir = run_dir / "psi"

        if psi_dir.exists():
            carpetas_h = [d for d in psi_dir.iterdir() if d.is_dir()]
            if len(carpetas_h) >= self._campos_esperados(norm):
                return True, run_dir, norm

        return False, run_dir, norm

    def listar_simulaciones_cacheadas(self) -> Dict[str, str]:
        """Devuelve un diccionario {Etiqueta legible: ruta} de todas las simulaciones en 'runs/'."""
        items: Dict[str, str] = {}
        if not self.runs_dir.exists():
            return items

        for carpeta in sorted(self.runs_dir.iterdir(), reverse=True):
            if not carpeta.is_dir():
                continue
            meta_file = carpeta / "metadata.json"
            psi_dir = carpeta / "psi"
            n_campos = len([d for d in psi_dir.iterdir() if d.is_dir()]) if psi_dir.exists() else 0
            if n_campos == 0:
                continue

            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    mod = meta.get("modelo", carpeta.name)
                    hi, hf, dh = meta.get("Hi", 0), meta.get("Hf", 0), meta.get("dH", 0.1)
                    if mod == "3D_1Banda":
                        etiqueta = (
                            f"[Caché {carpeta.name[-6:]}] {mod} | H={hi}..{hf} (dH={dh}) "
                            f"| {meta.get('suavizado_bordes')} | ({n_campos} pasos)"
                        )
                    else:
                        etiqueta = (
                            f"[Caché {carpeta.name[-6:]}] {mod} | H={hi}..{hf} (dH={dh}) "
                            f"| Gap={meta.get('Gap')} | ({n_campos} pasos)"
                        )
                    items[etiqueta] = str(carpeta)
                except Exception:
                    items[f"Simulación {carpeta.name} ({n_campos} pasos)"] = str(carpeta)
            else:
                items[f"Simulación {carpeta.name} ({n_campos} pasos)"] = str(carpeta)

        return items

    def generar_configuracion(self, norm: Dict[str, Any], run_dir: Path) -> Path:
        """Escribe config_simulacion.m y guarda metadata.json en la carpeta de la corrida."""
        run_dir.mkdir(parents=True, exist_ok=True)
        meta_path = run_dir / "metadata.json"
        meta_path.write_text(json.dumps(norm, indent=2), encoding="utf-8")

        cfg_dict = dict(norm)
        cfg_dict["is_restart"] = False
        cfg_dict["output_dir"] = str(run_dir).replace("\\", "/")
        cfg_dict["graficar_en_vivo"] = False
        cfg_dict["guardar_campos_extra"] = False

        config_path = self.engine_dir / "config_simulacion.m"
        lines = [
            "function cfg = config_simulacion()",
            "% CONFIG_SIMULACION Generado automáticamente desde Python (tdgl_solver).",
        ]

        for key, val in cfg_dict.items():
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

    def ejecutar_con_progreso(
        self,
        params: Dict[str, Any],
        callback_linea: Optional[Callable[[str], None]] = None,
        forzar_recalculo: bool = False,
    ) -> Tuple[Path, bool]:
        """Ejecuta la simulación en Octave transmitiendo el progreso línea a línea.

        Returns:
            Tuple[Path, bool]: (Ruta de salida, True si provino del caché sin recalcular).
        """
        ya_existe, run_dir, norm = self.verificar_cache(params)
        if ya_existe and not forzar_recalculo:
            return run_dir, True

        self.generar_configuracion(norm, run_dir)
        main_script = self.engine_dir / "main.m"
        cmd = ["octave", "--no-gui", "--quiet", str(main_script)]

        proceso = subprocess.Popen(
            cmd,
            cwd=str(self.engine_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if proceso.stdout:
            for linea in iter(proceso.stdout.readline, ""):
                linea_limpia = linea.rstrip()
                if linea_limpia and callback_linea:
                    callback_linea(linea_limpia)

        ret = proceso.wait()
        if ret != 0:
            raise RuntimeError(f"GNU Octave finalizó con código de error {ret}.")

        return run_dir, False