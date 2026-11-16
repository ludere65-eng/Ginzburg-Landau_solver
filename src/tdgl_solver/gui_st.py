"""
Interfaz web interactiva usando Streamlit para configuración, visualización
múltiple y animación de resultados TDGL respecto al campo magnético H.
"""

import time
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from tdgl_solver.io_handler import TDGLDataLoader

# 1. Configuración general de la página
st.set_page_config(
    page_title="TDGL Solver | Panel de Análisis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Diccionario que mapea nombres amigables con las rutas reales en disco
RUTAS_MODELOS: Dict[str, str] = {
    "Modularizado": "output_modular",
    "2D_2bandas sin modularizar": "Codigo2/output",
    "3D_1banda sin modularizar": "Codigo3/output",
}

# Nombres descriptivos para mejorar la presentación en la interfaz
NOMBRES_VARIABLES: Dict[str, str] = {
    "d": "Densidad Banda 1 (|ψ₁| o log|ψ|)",
    "B": "Densidad Banda 2 (|ψ₂|)",
    "d4": "Parámetro de Orden 3D (|ψ|)",
    "d2": "Logaritmo Parámetro de Orden (log|ψ|)",
    "hz": "Campo Magnético Local (Bz)",
    "phase": "Fase Superconductora (θ)",
    "aJx": "Supercorriente Transversal X (Jx)",
    "aJy": "Supercorriente Transversal Y (Jy)",
}


def construir_figura(
    matriz: np.ndarray,
    var_key: str,
    h_val: str,
    z_idx: int,
    cmap_name: str,
    fijar_escala: bool,
) -> plt.Figure:
    """Genera una figura estilizada de Matplotlib para una variable 2D o 3D."""
    if matriz.ndim == 3:
        vista = matriz[:, :, z_idx]
        subtitulo = f"H = {h_val} | Corte Z = {z_idx}"
    else:
        vista = matriz
        subtitulo = f"H = {h_val}"

    fig, ax = plt.subplots(figsize=(3.5, 3.0), dpi=110)

    # Fijar límites de escala ayuda a que la animación no parpadee al cambiar H
    vmin, vmax = None, None
    if fijar_escala:
        if var_key in ("d4", "B"):
            vmin, vmax = 0.0, 1.0
        elif var_key == "phase":
            vmin, vmax = -np.pi, np.pi

    im = ax.imshow(
        vista,
        cmap=cmap_name,
        origin="lower",
        vmin=vmin,
        vmax=vmax,
        aspect="equal",
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=8)

    titulo_legible = NOMBRES_VARIABLES.get(var_key, var_key)
    ax.set_title(f"{titulo_legible}\n({subtitulo})", fontsize=10, fontweight="bold")
    ax.set_xlabel("x (celdas)", fontsize=8)
    ax.set_ylabel("y (celdas)", fontsize=8)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return fig


def main() -> None:
    st.title("Simulador Ginzburg-Landau (TDGL) — Análisis Visual")
    st.markdown(
        "Explora la dinámica de vórtices, distribución de campo magnético y corrientes "
        "superconductoras de forma simultánea o animada."
    )

    # --- PANEL LATERAL DE CONFIGURACIÓN ---
    st.sidebar.header("1. Fuente de Datos")
    opcion_modelo = st.sidebar.selectbox(
        "Selecciona el conjunto de simulación:",
        options=list(RUTAS_MODELOS.keys()),
    )
    ruta_real = RUTAS_MODELOS[opcion_modelo]

    # Buscar la ruta relativa desde el directorio actual o desde la raíz del proyecto
    ruta_path = Path(ruta_real)
    if not ruta_path.exists():
        # Intentar buscar dos niveles arriba si se ejecuta desde src/tdgl_solver/
        ruta_alt = Path(__file__).resolve().parents[2] / ruta_real
        if ruta_alt.exists():
            ruta_path = ruta_alt

    try:
        loader = TDGLDataLoader(str(ruta_path))
        campos = loader.listar_campos_disponibles()
    except FileNotFoundError:
        st.error(
            f"No se encontró la carpeta `{ruta_real}` para **{opcion_modelo}**. "
            "Verifica que la simulación se haya ejecutado o que los archivos `.mat` existan."
        )
        return

    if not campos:
        st.warning(f"La carpeta `{ruta_real}` está vacía. Ejecuta una simulación primero.")
        return

    # Inspeccionar el primer campo para conocer qué variables y dimensiones hay
    datos_muestra = loader.cargar_paso_campo(campos[0])
    vars_disponibles = list(datos_muestra.keys())
    es_3d = any(mat.ndim == 3 for mat in datos_muestra.values())

    st.sidebar.header("2. Variables y Apariencia")
    vars_seleccionadas: List[str] = st.sidebar.multiselect(
        "Variables a visualizar simultáneamente:",
        options=vars_disponibles,
        default=vars_disponibles[: min(2, len(vars_disponibles))],
        format_func=lambda k: NOMBRES_VARIABLES.get(k, k),
    )

    cmap_elegido = st.sidebar.selectbox(
        "Paleta de colores:",
        options=["inferno", "viridis", "plasma", "magma", "twilight", "coolwarm"],
        index=0,
    )

    fijar_escala = st.sidebar.checkbox(
        "Fijar escala de color (recomendado para animaciones)",
        value=True,
    )

    z_slice = 0
    if es_3d:
        max_z = max(mat.shape[2] for mat in datos_muestra.values() if mat.ndim == 3) - 1
        st.sidebar.header("3. Corte Transversal 3D")
        z_slice = st.sidebar.slider("Plano Z:", 0, max_z, max_z // 2)

    st.sidebar.header("4. Control de Campo Magnético (H)")
    modo_animacion = st.sidebar.toggle("Modo Animación (Evolución en H)", value=False)

    if not vars_seleccionadas:
        st.info("Selecciona al menos una variable en el menú lateral para graficar.")
        return

    # --- RENDERIZADO ESTÁTICO O ANIMADO ---
    contenedor_graficas = st.empty()

    def renderizar_cuadricula(h_actual: str) -> None:
        datos = loader.cargar_paso_campo(h_actual)
        with contenedor_graficas.container():
            st.subheader(f"Estado Estacionario para Campo Aplicado H = {h_actual}")
            # Organizar en cuadrícula de máximo 2 columnas por fila para buena visibilidad
            num_cols = min(3, len(vars_seleccionadas))
            cols = st.columns(num_cols)

            for idx, var_key in enumerate(vars_seleccionadas):
                if var_key in datos:
                    fig = construir_figura(
                        datos[var_key],
                        var_key,
                        h_actual,
                        z_slice,
                        cmap_elegido,
                        fijar_escala,
                    )
                    with cols[idx % num_cols]:
                        st.pyplot(fig, use_container_width=False)
                    plt.close(fig)  # Libera memoria RAM en cada fotograma

    if not modo_animacion:
        h_seleccionado = st.sidebar.select_slider(
            "Valor de Campo H:",
            options=campos,
            value=campos[0],
        )
        renderizar_cuadricula(h_seleccionado)
    else:
        velocidad = st.sidebar.slider(
            "Pausa entre fotogramas (segundos):",
            min_value=0.05,
            max_value=1.50,
            value=0.30,
            step=0.05,
        )
        repetir = st.sidebar.checkbox("Bucle continuo", value=False)

        if st.sidebar.button("Iniciar Animación", type="primary"):
            barra_progreso = st.progress(0)
            while True:
                for i, h_val in enumerate(campos):
                    renderizar_cuadricula(h_val)
                    barra_progreso.progress((i + 1) / len(campos))
                    time.sleep(velocidad)
                if not repetir:
                    break
            st.success("Secuencia de evolución magnética completada.")
        else:
            st.info("Presiona **Iniciar Animación** en el panel lateral para reproducir la evolución de H.")
            renderizar_cuadricula(campos[0])


if __name__ == "__main__":
    main()