"""
Suite de pruebas unitarias (10 tests) para el paquete TDGL Solver.
"""

import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
import scipy.io as sio

from tdgl_solver.runner import TDGLRunner
from tdgl_solver.io_handler import TDGLDataLoader


# =====================================================================
# PRUEBAS PARA EL ORQUESTADOR Y CACHÉ (TDGLRunner)
# =====================================================================

def test_1_normalizacion_parametros_2d(tmp_path: Path):
    """Verifica que los parámetros por defecto de 2D se asignen correctamente."""
    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    params_in = {"modelo": "2D_2Bandas", "dx": 0.25}
    norm = runner.normalizar_parametros(params_in)

    assert norm["a"] == 10.0  # Valor por defecto 2D
    assert norm["b"] == 10.0
    assert norm["eps"] == 1e-5
    assert norm["Gap"] == -0.001
    assert norm["dz"] == 0.25  # Valor neutro inyectado para compatibilidad con Octave


def test_2_normalizacion_parametros_3d(tmp_path: Path):
    """Verifica que los parámetros exclusivos y por defecto de 3D se asignen correctamente."""
    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    params_in = {"modelo": "3D_1Banda", "dx": 0.2, "suavizado_bordes": "ambos"}
    norm = runner.normalizar_parametros(params_in)

    assert norm["a"] == 20.0  # Valor por defecto 3D
    assert norm["dz"] == 0.25
    assert norm["eps"] == 1e-7
    assert norm["suavizado_bordes"] == "ambos"
    assert norm["Gap"] == -0.001


def test_3_hash_unico_por_parametros(tmp_path: Path):
    """Verifica que el hash (SHA-256) cambie si y solo si cambian los parámetros."""
    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    p1 = {"modelo": "2D_2Bandas", "Hi": 0.0, "Hf": 1.0}
    p2 = {"modelo": "2D_2Bandas", "Hf": 1.0, "Hi": 0.0}  # Mismos parámetros, distinto orden
    p3 = {"modelo": "2D_2Bandas", "Hi": 0.0, "Hf": 1.5}  # Diferente Hf

    id1, _, _ = runner.calcular_hash_y_ruta(p1)
    id2, _, _ = runner.calcular_hash_y_ruta(p2)
    id3, _, _ = runner.calcular_hash_y_ruta(p3)

    assert id1 == id2
    assert id1 != id3


def test_4_verificar_cache_no_existente(tmp_path: Path):
    """Verifica el comportamiento cuando la simulación nunca se ha ejecutado."""
    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    params = {"modelo": "2D_2Bandas", "Hi": 0.0, "Hf": 0.1, "dH": 0.1}

    existe, run_dir, _ = runner.verificar_cache(params)

    assert existe is False
    assert run_dir.parent == tmp_path


def test_5_verificar_cache_existente_y_completo(tmp_path: Path):
    """Verifica que el sistema detecte una corrida completa exitosamente."""
    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    params = {"modelo": "2D_2Bandas", "Hi": 0.0, "Hf": 0.1, "dH": 0.1}

    _, run_dir, norm = runner.calcular_hash_y_ruta(params)
    (run_dir / "psi" / "0.0").mkdir(parents=True)
    (run_dir / "psi" / "0.1").mkdir(parents=True)
    (run_dir / "metadata.json").write_text(json.dumps(norm), encoding="utf-8")

    existe, _, _ = runner.verificar_cache(params)
    assert existe is True


def test_6_generacion_archivo_configuracion_octave(tmp_path: Path):
    """Verifica la correcta escritura del archivo config_simulacion.m."""
    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    params = {"modelo": "3D_1Banda", "kappa": 1.5}
    _, run_dir, norm = runner.calcular_hash_y_ruta(params)

    config_file = runner.generar_configuracion(norm, run_dir)

    assert config_file.exists()
    contenido = config_file.read_text(encoding="utf-8")
    assert "function cfg = config_simulacion()" in contenido
    assert "cfg.modelo = '3D_1Banda';" in contenido
    assert "cfg.kappa = 1.5;" in contenido
    assert "cfg.is_restart = false;" in contenido


@patch("tdgl_solver.runner.subprocess.Popen")
def test_7_ejecucion_octave_mockeada(mock_popen, tmp_path: Path):
    """Prueba la ejecución de Octave capturando stdout en streaming sin lanzar el binario real."""
    mock_proceso = MagicMock()
    mock_proceso.stdout = io.StringIO(
        "Iniciando simulacion...\nCampo H = 0.0 completado en 1.5 s\n"
    )
    mock_proceso.wait.return_value = 0
    mock_popen.return_value = mock_proceso

    runner = TDGLRunner(base_runs_dir=str(tmp_path))
    params = {"modelo": "2D_2Bandas", "Hi": 0.0, "Hf": 0.0, "dH": 0.1}

    lineas_capturadas = []
    out_dir, cache_hit = runner.ejecutar_con_progreso(
        params, callback_linea=lineas_capturadas.append
    )

    assert cache_hit is False
    assert out_dir.exists()
    assert len(lineas_capturadas) == 2
    assert "completado en 1.5 s" in lineas_capturadas[1]
    mock_popen.assert_called_once()


# =====================================================================
# PRUEBAS PARA EL LECTOR DE DATOS (TDGLDataLoader)
# =====================================================================

def test_8_dataloader_lista_campos_ordenados(tmp_path: Path):
    """Verifica que el cargador detecte y ordene numéricamente los pasos de H."""
    psi_dir = tmp_path / "psi"
    for h in ["1.0", "0.2", "0.1", "2.0"]:
        (psi_dir / h).mkdir(parents=True)

    loader = TDGLDataLoader(str(tmp_path))
    campos = loader.listar_campos_disponibles()

    assert campos == ["0.1", "0.2", "1.0", "2.0"]


def test_9_dataloader_carga_matrices_2d(tmp_path: Path):
    """Verifica la lectura correcta de archivos .mat generados por Octave."""
    (tmp_path / "psi" / "0.5").mkdir(parents=True)
    (tmp_path / "field" / "0.5").mkdir(parents=True)

    mat_d = np.ones((81, 81))
    mat_hz = np.zeros((80, 80))

    sio.savemat(tmp_path / "psi" / "0.5" / "d.mat", {"d": mat_d})
    sio.savemat(tmp_path / "field" / "0.5" / "hz.mat", {"hz": mat_hz})

    loader = TDGLDataLoader(str(tmp_path))
    datos = loader.cargar_paso_campo("0.5")

    assert "d" in datos
    assert "hz" in datos
    assert datos["d"].shape == (81, 81)
    assert datos["hz"].shape == (80, 80)
    assert np.all(datos["d"] == 1.0)


def test_10_dataloader_directorio_invalido():
    """Verifica el manejo de errores al intentar cargar rutas inexistentes."""
    ruta_falsa = Path("/ruta/que/no/existe/jamas/123")

    with pytest.raises(FileNotFoundError) as excinfo:
        TDGLDataLoader(str(ruta_falsa))

    assert "No se encontró el directorio" in str(excinfo.value)