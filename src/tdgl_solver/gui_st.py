"""
Interfaz web interactiva en Streamlit para simular (con detección de caché)
y visualizar/animar resultados TDGL en 2D (2 bandas) y 3D (1 banda).
"""

import time
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from tdgl_solver.io_handler import TDGLDataLoader
from tdgl_solver.runner import TDGLRunner

st.set_page_config(
    page_title="TDGL Solver | Simulación y Análisis",
    layout="wide",
    initial_sidebar_state="expanded",
)

RUTAS_BASE: Dict[str, str] = {
    "Modularizado": "output_modular",
    "2D_2bandas sin modularizar": "Codigo2/output",
    "3D_1banda sin modularizar": "Codigo3/output",
}

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


def resolver_ruta(ruta_str: str) -> Path:
    p = Path(ruta_str)
    if p.exists():
        return p
    p_alt = Path(__file__).resolve().parents[2] / ruta_str
    return p_alt


def construir_figura(
    matriz: np.ndarray,
    var_key: str,
    h_val: str,
    z_idx: int,
    cmap_name: str,
    fijar_escala: bool,
) -> plt.Figure:
    if matriz.ndim == 3:
        vista = matriz[:, :, z_idx]
        subtitulo = f"H = {h_val} | Z = {z_idx}"
    else:
        vista = matriz
        subtitulo = f"H = {h_val}"

    fig, ax = plt.subplots(figsize=(3.5, 3.0), dpi=110)

    vmin, vmax = None, None
    if fijar_escala:
        if var_key in ("d4", "B"):
            vmin, vmax = 0.0, 1.0
        elif var_key == "phase":
            vmin, vmax = -np.pi, np.pi

    im = ax.imshow(
        vista, cmap=cmap_name, origin="lower", vmin=vmin, vmax=vmax, aspect="equal"
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=7)

    titulo = NOMBRES_VARIABLES.get(var_key, var_key)
    ax.set_title(f"{titulo}\n({subtitulo})", fontsize=8.5, fontweight="bold")
    ax.set_xlabel("x", fontsize=7)
    ax.set_ylabel("y", fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def mostrar_panel_simulacion(runner: TDGLRunner) -> None:
    st.subheader("Configurar y Ejecutar Nueva Simulación TDGL")
    st.markdown(
        "Selecciona la arquitectura del modelo. El sistema verificará automáticamente "
        "si ya existe una simulación con los mismos parámetros para mostrarte el "
        "resultado sin recalcular."
    )

    modelo = st.radio(
        "Arquitectura del Modelo:",
        options=["2D_2Bandas", "3D_1Banda"],
        horizontal=True,
    )

    col_geom, col_fis, col_mag = st.columns(3)

    with col_geom:
        st.markdown("#### 1. Geometría y Malla")
        dx = st.number_input("Paso espacial dx:", value=0.25, min_value=0.05, step=0.05)
        dy = st.number_input("Paso espacial dy:", value=0.25, min_value=0.05, step=0.05)
        a = st.number_input(
            "Tamaño caja externa X (a):",
            value=10.0 if modelo == "2D_2Bandas" else 20.0,
            min_value=1.0,
            step=1.0,
        )
        b = st.number_input(
            "Tamaño caja externa Y (b):",
            value=10.0 if modelo == "2D_2Bandas" else 20.0,
            min_value=1.0,
            step=1.0,
        )

        if modelo == "3D_1Banda":
            dz = st.number_input("Paso espacial dz:", value=0.25, min_value=0.05, step=0.05)
            c = st.number_input("Tamaño caja externa Z (c):", value=10.0, min_value=1.0, step=1.0)
            aa = st.number_input("Caja interna X (aa):", value=10.0, min_value=1.0, step=1.0)
            bb = st.number_input("Caja interna Y (bb):", value=10.0, min_value=1.0, step=1.0)
            cc = st.number_input("Caja interna Z (cc):", value=5.0, min_value=1.0, step=1.0)

    with col_fis:
        st.markdown("#### 2. Parámetros Físicos")
        kappa = st.number_input("Parámetro Ginzburg-Landau (κ):", value=1.0, min_value=0.1, step=0.1)
        bt = st.number_input("Coeficiente de relajación (β):", value=1.0, min_value=0.1, step=0.1)
        T = st.number_input("Temperatura reducida (T/Tc):", value=0.0, min_value=0.0, max_value=0.99, step=0.05)

        if modelo == "2D_2Bandas":
            Gap = st.number_input(
                "Acoplamiento interbanda (Gap):",
                value=-0.001,
                step=0.001,
                format="%.4f",
            )
        else:
            geometria_tau = st.selectbox(
                "Geometría de enlaces (tau):",
                options=["bloque", "estricto"],
            )
            suavizado_bordes = st.selectbox(
                "Suavizado en fronteras 3D:",
                options=["8_vertices", "12_aristas", "ambos"],
            )

    with col_mag:
        st.markdown("#### 3. Campo Magnético y Convergencia")
        Hi = st.number_input("Campo inicial (Hi):", value=0.0, step=0.1)
        Hf = st.number_input("Campo final (Hf):", value=0.2, step=0.1)
        dH = st.number_input("Paso de campo (dH):", value=0.1, min_value=0.01, step=0.05)
        eps = st.number_input(
            "Tolerancia (eps):",
            value=1e-5 if modelo == "2D_2Bandas" else 1e-7,
            format="%.1e",
        )
        nMax = st.number_input("Iteraciones máximas (nMax):", value=10000000, step=100000)
        lMax = st.number_input("Sub-iteraciones internas (lMax):", value=100, step=10)

    params: Dict[str, Any] = {
        "modelo": modelo,
        "dx": dx,
        "dy": dy,
        "a": a,
        "b": b,
        "kappa": kappa,
        "bt": bt,
        "T": T,
        "Hi": Hi,
        "Hf": Hf,
        "dH": dH,
        "eps": eps,
        "nMax": int(nMax),
        "lMax": int(lMax),
    }
    if modelo == "3D_1Banda":
        params.update(
            {
                "dz": dz,
                "c": c,
                "aa": aa,
                "bb": bb,
                "cc": cc,
                "geometria_tau": geometria_tau,
                "suavizado_bordes": suavizado_bordes,
            }
        )
    else:
        params.update({"Gap": Gap})

    # Verificar estado en caché antes de ejecutar
    en_cache, ruta_esperada, norm = runner.verificar_cache(params)
    if en_cache:
        st.success(
            f"⚡ **Estos parámetros ya fueron ejecutados previamente.** "
            f"Los resultados están listos en `{ruta_esperada.name}`."
        )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        iniciar = st.button("🚀 Simular / Cargar Resultados", type="primary", use_container_width=True)
    with col_btn2:
        forzar = st.checkbox("Forzar recálculo aunque exista en caché", value=False)

    if iniciar:
        if en_cache and not forzar:
            st.session_state["ruta_activa_override"] = str(ruta_esperada)
            st.toast("Cargando resultados directamente desde el caché...", icon="✅")
            st.info(
                "Ve a la pestaña **📊 Visualizador y Animación** (arriba) para explorar las gráficas."
            )
        else:
            st.warning(
                f"Ejecutando motor GNU Octave en `{ruta_esperada.name}`. "
                "Cada paso de campo H se guarda en disco apenas converge..."
            )
            barra = st.progress(0)
            caja_log = st.empty()
            lineas_log: List[str] = []
            total_pasos = max(1, int(round((norm["Hf"] - norm["Hi"]) / norm["dH"])) + 1)
            pasos_completados = 0

            def procesar_linea(linea: str) -> None:
                nonlocal pasos_completados
                lineas_log.append(linea)
                caja_log.code("\n".join(lineas_log[-12:]), language="text")
                if "completado en" in linea:
                    pasos_completados += 1
                    barra.progress(min(1.0, pasos_completados / total_pasos))

            try:
                out_dir, _ = runner.ejecutar_con_progreso(
                    params, callback_linea=procesar_linea, forzar_recalculo=forzar
                )
                barra.progress(1.0)
                st.session_state["ruta_activa_override"] = str(out_dir)
                st.success(
                    f"✅ Simulación completada y guardada en `{out_dir.name}`. "
                    "Pasa a la pestaña **📊 Visualizador y Animación** para ver las gráficas."
                )
            except Exception as e:
                st.error(f"Error durante la simulación: {e}")


def main() -> None:
    st.title("Simulador Ginzburg-Landau (TDGL) — Suite Interactiva")
    runner = TDGLRunner()

    tab_vis, tab_sim = st.tabs(
        ["📊 Visualizador y Animación", "⚙️ Nueva Simulación (Cálculo)"]
    )

    with tab_sim:
        mostrar_panel_simulacion(runner)

    with tab_vis:
        # Combinar las 3 opciones fijas con las simulaciones cacheadas en runs/
        opciones_totales: Dict[str, str] = dict(RUTAS_BASE)
        opciones_totales.update(runner.listar_simulaciones_cacheadas())

        st.sidebar.header("1. Fuente de Datos")
        nombres_opciones = list(opciones_totales.keys())

        # Si acaba de correr o cargar una simulación, seleccionarla automáticamente
        idx_default = 0
        if "ruta_activa_override" in st.session_state:
            ruta_over = st.session_state["ruta_activa_override"]
            for i, k in enumerate(nombres_opciones):
                if Path(opciones_totales[k]).resolve() == Path(ruta_over).resolve():
                    idx_default = i
                    break

        opcion_modelo = st.sidebar.selectbox(
            "Conjunto de simulación:",
            options=nombres_opciones,
            index=idx_default,
        )
        ruta_path = resolver_ruta(opciones_totales[opcion_modelo])

        try:
            loader = TDGLDataLoader(str(ruta_path))
            campos = loader.listar_campos_disponibles()
        except FileNotFoundError:
            st.error(f"No se encontró la carpeta para **{opcion_modelo}**.")
            return

        if not campos:
            st.warning("Esta carpeta aún no tiene pasos de campo H guardados.")
            return

        datos_muestra = loader.cargar_paso_campo(campos[0])
        vars_disponibles = list(datos_muestra.keys())
        es_3d = any(mat.ndim == 3 for mat in datos_muestra.values())

        st.sidebar.header("2. Variables y Apariencia")
        vars_seleccionadas: List[str] = st.sidebar.multiselect(
            "Variables a visualizar:",
            options=vars_disponibles,
            default=vars_disponibles[: min(2, len(vars_disponibles))],
            format_func=lambda k: NOMBRES_VARIABLES.get(k, k),
        )

        cmap_elegido = st.sidebar.selectbox(
            "Paleta de colores:",
            options=["inferno", "viridis", "plasma", "magma", "twilight", "coolwarm"],
            index=0,
        )
        fijar_escala = st.sidebar.checkbox("Fijar escala de color", value=True)

        z_slice = 0
        if es_3d:
            max_z = max(mat.shape[2] for mat in datos_muestra.values() if mat.ndim == 3) - 1
            st.sidebar.header("3. Corte Transversal 3D")
            z_slice = st.sidebar.slider("Plano Z:", 0, max_z, max_z // 2)

        st.sidebar.header("4. Control de Campo H")
        modo_animacion = st.sidebar.toggle("Modo Animación (Evolución en H)", value=False)

        if not vars_seleccionadas:
            st.info("Selecciona al menos una variable en el menú lateral.")
            return

        contenedor_graficas = st.empty()

        def renderizar_cuadricula(h_actual: str) -> None:
            datos = loader.cargar_paso_campo(h_actual)
            with contenedor_graficas.container():
                st.markdown(f"**Conjunto:** `{opcion_modelo}` — **Campo Aplicado H = {h_actual}**")
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
                        plt.close(fig)

        if not modo_animacion:
            h_seleccionado = st.sidebar.select_slider(
                "Valor de Campo H:", options=campos, value=campos[0]
            )
            renderizar_cuadricula(h_seleccionado)
        else:
            velocidad = st.sidebar.slider(
                "Pausa entre cuadros (s):", 0.05, 1.50, 0.30, 0.05
            )
            repetir = st.sidebar.checkbox("Bucle continuo", value=False)
            if st.sidebar.button("▶ Iniciar Animación", type="primary"):
                barra_anim = st.progress(0)
                while True:
                    for i, h_val in enumerate(campos):
                        renderizar_cuadricula(h_val)
                        barra_anim.progress((i + 1) / len(campos))
                        time.sleep(velocidad)
                    if not repetir:
                        break
            else:
                renderizar_cuadricula(campos[0])


if __name__ == "__main__":
    main()