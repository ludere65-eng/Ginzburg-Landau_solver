# src/tdgl_solver/gui_st.py

"""
Interfaz web interactiva completa en Streamlit para simulación TDGL (con caché)
y análisis avanzado (cuadrículas, mapas interactivos, vectores, estadística y 3D).
"""

import time
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

from tdgl_solver.io_handler import TDGLDataLoader
from tdgl_solver.runner import TDGLRunner


st.set_page_config(
    page_title="TDGL Solver | Suite de Simulación y Análisis",
    layout="wide",
    initial_sidebar_state="expanded",
)

RUTAS_BASE: Dict[str, str] = {
    "Modularizado": "output_modular",
    "2D_2bandas sin modularizar": "Codigo2/output",
    "3D_1banda sin modularizar": "Codigo3/output",
}

NOMBRES_VARIABLES: Dict[str, str] = {
    "d": "Densidad Banda 1 (|ψ₁|)",
    "B": "Densidad Banda 2 (|ψ₂|)",
    "d4": "Parámetro Orden 3D (|ψ|)",
    "d2": "Logaritmo Orden (log|ψ|)",
    "hz": "Campo Magnético (Bz)",
    "phase": "Fase Superconductora (θ)",
    "aJx": "Supercorriente X (Jx)",
    "aJy": "Supercorriente Y (Jy)",
}


def resolver_ruta(ruta_str: str) -> Path:
    p = Path(ruta_str)
    if p.exists():
        return p
    return Path(__file__).resolve().parents[2] / ruta_str


def construir_figura_base(
    matriz: np.ndarray,
    var_key: str,
    h_val: str,
    z_idx: int,
    cmap_name: str,
    fijar_escala: bool,
) -> plt.Figure:
    """Genera figura Matplotlib compacta para la cuadrícula y animación."""
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
    st.subheader("⚙️ Configurar y Ejecutar Nueva Simulación TDGL")
    st.markdown(
        "El sistema verificará automáticamente si ya existe una simulación "
        "con los mismos parámetros y cargará los resultados desde la memoria caché."
    )

    modelo = st.radio(
        "Arquitectura del Modelo:", options=["2D_2Bandas", "3D_1Banda"], horizontal=True
    )

    col_geom, col_fis, col_mag = st.columns(3)

    with col_geom:
        st.markdown("#### 1. Geometría y Malla")
        dx = st.number_input("Paso espacial dx:", value=0.25, step=0.05)
        dy = st.number_input("Paso espacial dy:", value=0.25, step=0.05)
        a = st.number_input(
            "Caja externa X (a):", value=10.0 if modelo == "2D_2Bandas" else 20.0, step=1.0
        )
        b = st.number_input(
            "Caja externa Y (b):", value=10.0 if modelo == "2D_2Bandas" else 20.0, step=1.0
        )
        if modelo == "3D_1Banda":
            dz = st.number_input("Paso espacial dz:", value=0.25, step=0.05)
            c = st.number_input("Caja externa Z (c):", value=10.0, step=1.0)
            aa = st.number_input("Caja interna X (aa):", value=10.0, step=1.0)
            bb = st.number_input("Caja interna Y (bb):", value=10.0, step=1.0)
            cc = st.number_input("Caja interna Z (cc):", value=5.0, step=1.0)

    with col_fis:
        st.markdown("#### 2. Parámetros Físicos")
        kappa = st.number_input("Parámetro G-L (κ):", value=1.0, step=0.1)
        bt = st.number_input("Relajación (β):", value=1.0, step=0.1)
        T = st.number_input("Temperatura (T/Tc):", value=0.0, max_value=0.99, step=0.05)
        if modelo == "2D_2Bandas":
            Gap = st.number_input("Acoplamiento (Gap):", value=-0.001, format="%.4f")
        else:
            geometria_tau = st.selectbox("Geometría enlaces (tau):", ["bloque", "estricto"])
            suavizado_bordes = st.selectbox(
                "Suavizado fronteras 3D:", ["8_vertices", "12_aristas", "ambos"]
            )

    with col_mag:
        st.markdown("#### 3. Control y Barrido H")
        Hi = st.number_input("Campo inicial (Hi):", value=0.0, step=0.1)
        Hf = st.number_input("Campo final (Hf):", value=0.2, step=0.1)
        dH = st.number_input("Paso de campo (dH):", value=0.1, step=0.05)
        eps = st.number_input(
            "Tolerancia (eps):", value=1e-5 if modelo == "2D_2Bandas" else 1e-7, format="%.1e"
        )
        nMax = st.number_input("Iteraciones máx (nMax):", value=10000000, step=100000)
        lMax = st.number_input("Sub-iteraciones (lMax):", value=100, step=10)

    params: Dict[str, Any] = {
        "modelo": modelo, "dx": dx, "dy": dy, "a": a, "b": b,
        "kappa": kappa, "bt": bt, "T": T, "Hi": Hi, "Hf": Hf,
        "dH": dH, "eps": eps, "nMax": int(nMax), "lMax": int(lMax),
    }
    if modelo == "3D_1Banda":
        params.update({
            "dz": dz, "c": c, "aa": aa, "bb": bb, "cc": cc,
            "geometria_tau": geometria_tau, "suavizado_bordes": suavizado_bordes,
        })
    else:
        params.update({"Gap": Gap})

    en_cache, ruta_esperada, norm = runner.verificar_cache(params)
    if en_cache:
        st.success(
            f"⚡ **Parámetros detectados en caché.** Resultados disponibles en `{ruta_esperada.name}`."
        )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        iniciar = st.button("🚀 Simular / Cargar", type="primary", use_container_width=True)
    with col_btn2:
        forzar = st.checkbox("Forzar recálculo", value=False)

    if iniciar:
        if en_cache and not forzar:
            st.session_state["ruta_activa"] = str(ruta_esperada)
            st.info("Pasa a la pestaña **📊 Visualizador Analítico** para ver las gráficas.")
        else:
            st.warning(f"Calculando en `{ruta_esperada.name}`. Guardando progresivamente...")
            barra = st.progress(0)
            caja_log = st.empty()
            log_lineas: List[str] = []
            tot_pasos = max(1, int(round((norm["Hf"] - norm["Hi"]) / norm["dH"])) + 1)
            pasos_ok = 0

            def callback(linea: str) -> None:
                nonlocal pasos_ok
                log_lineas.append(linea)
                caja_log.code("\n".join(log_lineas[-10:]), language="text")
                if "completado en" in linea:
                    pasos_ok += 1
                    barra.progress(min(1.0, pasos_ok / tot_pasos))

            try:
                out_dir, _ = runner.ejecutar_con_progreso(
                    params, callback_linea=callback, forzar_recalculo=forzar
                )
                barra.progress(1.0)
                st.session_state["ruta_activa"] = str(out_dir)
                st.success("✅ Simulación completada.")
            except Exception as e:
                st.error(f"Error: {e}")


def main() -> None:
    st.title("Simulador TDGL — Plataforma de Análisis Integral")
    runner = TDGLRunner()

    tab_vis, tab_sim = st.tabs([
        "📊 Visualizador Analítico Multivariable", 
        "⚙️ Nueva Simulación (Cálculo)"
    ])

    with tab_sim:
        mostrar_panel_simulacion(runner)

    with tab_vis:
        ops_totales: Dict[str, str] = dict(RUTAS_BASE)
        ops_totales.update(runner.listar_simulaciones_cacheadas())

        st.sidebar.header("1. Selección de Datos")
        nombres_opc = list(ops_totales.keys())

        idx_def = 0
        if "ruta_activa" in st.session_state:
            ra = st.session_state["ruta_activa"]
            for i, k in enumerate(nombres_opc):
                if Path(ops_totales[k]).resolve() == Path(ra).resolve():
                    idx_def = i
                    break

        opcion_modelo = st.sidebar.selectbox("Conjunto de simulación:", options=nombres_opc, index=idx_def)
        ruta_path = resolver_ruta(ops_totales[opcion_modelo])

        try:
            loader = TDGLDataLoader(str(ruta_path))
            campos = loader.listar_campos_disponibles()
        except FileNotFoundError:
            st.error(f"No se encontró el directorio para **{opcion_modelo}**.")
            return

        if not campos:
            st.warning("Carpeta vacía (sin pasos H guardados).")
            return

        datos_test = loader.cargar_paso_campo(campos[0])
        vars_disp = list(datos_test.keys())
        es_3d = any(mat.ndim == 3 for mat in datos_test.values())

        st.sidebar.header("2. Opciones Base")
        vars_sel: List[str] = st.sidebar.multiselect(
            "Variables activas:", options=vars_disp, default=vars_disp[:min(2, len(vars_disp))],
            format_func=lambda k: NOMBRES_VARIABLES.get(k, k)
        )
        cmap_elegido = st.sidebar.selectbox("Paleta (Mapas 2D):", ["inferno", "viridis", "plasma", "coolwarm", "RdBu_r"], index=0)
        fijar_escala = st.sidebar.checkbox("Fijar escala (Recomendado para animación)", value=True)

        z_slice = 0
        if es_3d:
            max_z = max(mat.shape[2] for mat in datos_test.values() if mat.ndim == 3) - 1
            st.sidebar.header("3. Corte Transversal Z")
            z_slice = st.sidebar.slider("Capa Z:", 0, max_z, max_z // 2)

        st.sidebar.header("4. Control H (Animación)")
        modo_anim = st.sidebar.toggle("Animar H (Aplica a Cuadrícula)", value=False)
        h_sel = campos[0]
        if not modo_anim:
            h_sel = st.sidebar.select_slider("Valor de Campo H (Gráficos estáticos):", options=campos, value=campos[0])
        else:
            vel = st.sidebar.slider("Pausa entre cuadros (s):", 0.05, 1.0, 0.2)
            repetir = st.sidebar.checkbox("Bucle continuo", value=False)
            btn_play = st.sidebar.button("▶ Reproducir", type="primary")

        if not vars_sel:
            st.info("Selecciona variables en el menú lateral.")
            return

        # Pestañas analíticas internas
        subtabs = st.tabs([
            "🖥️ Cuadrícula Base", 
            "🗺️ Plotly: Interactivo", 
            "↗️ Flujo y Vectores", 
            "📈 Estadística y Correlación", 
            "🧊 Reconstrucción 3D"
        ])

        datos = loader.cargar_paso_campo(h_sel)

        # -----------------------------------------------------------------
        # 1. CUADRÍCULA BASE (Matplotlib - Soporta Animación Nativa)
        # -----------------------------------------------------------------
        with subtabs[0]:
            cont_grid = st.empty()

            def dibujar_grid(h_val: str):
                dts = loader.cargar_paso_campo(h_val)
                with cont_grid.container():
                    st.markdown(f"**H = {h_val}**")
                    cols = st.columns(min(3, len(vars_sel)))
                    for idx, vkey in enumerate(vars_sel):
                        if vkey in dts:
                            fig = construir_figura_base(dts[vkey], vkey, h_val, z_slice, cmap_elegido, fijar_escala)
                            with cols[idx % len(cols)]:
                                st.pyplot(fig, use_container_width=False)
                            plt.close(fig)

            if modo_anim and btn_play:
                barra_anim = st.progress(0)
                while True:
                    for i, hv in enumerate(campos):
                        dibujar_grid(hv)
                        barra_anim.progress((i + 1) / len(campos))
                        time.sleep(vel)
                    if not repetir:
                        break
            else:
                dibujar_grid(h_sel)

        # -----------------------------------------------------------------
        # 2. PLOTLY: MAPAS INTERACTIVOS
        # -----------------------------------------------------------------
        with subtabs[1]:
            st.markdown("Gráficos interactivos con hover, zoom y paneo (Estado estático actual).")
            col1, col2 = st.columns(2)
            
            var_c1 = vars_sel[0] if len(vars_sel) > 0 else vars_disp[0]
            var_c2 = vars_sel[1] if len(vars_sel) > 1 else vars_disp[-1]

            for i, (col, vk) in enumerate(zip([col1, col2], [var_c1, var_c2])):
                if vk in datos:
                    vista = datos[vk][:, :, z_slice] if es_3d else datos[vk]
                    if i == 0:
                        fig = go.Figure(data=go.Contour(z=vista, colorscale=cmap_elegido.capitalize(), contours=dict(showlines=False)))
                        fig.update_layout(title=f"Contorno: {NOMBRES_VARIABLES.get(vk, vk)}")
                    else:
                        fig = px.imshow(vista, color_continuous_scale="RdBu_r", title=f"Mapa de Calor: {NOMBRES_VARIABLES.get(vk, vk)}")
                    col.plotly_chart(fig, use_container_width=True)

        # -----------------------------------------------------------------
        # 3. FLUJO Y VECTORES
        # -----------------------------------------------------------------
        with subtabs[2]:
            st.markdown("Análisis vectorial de supercorrientes.")
            if "aJx" in datos and "aJy" in datos:
                jx = datos["aJx"][:, :, z_slice] if es_3d else datos["aJx"]
                jy = datos["aJy"][:, :, z_slice] if es_3d else datos["aJy"]

                # Quiver interactivo (Reducir densidad de vectores para rendimiento)
                x, y = np.meshgrid(np.arange(0, jx.shape[1], 2), np.arange(0, jx.shape[0], 2))
                u, v = jx[::2, ::2], jy[::2, ::2]
                
                fig_q = ff.create_quiver(x, y, u, v, scale=0.5, arrow_scale=0.3, name='J', line_color='crimson')
                fig_q.update_layout(title="Quiver Plot (Vectores J)", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_q, use_container_width=True)

                # Streamplot de Matplotlib
                fig_st, ax_st = plt.subplots(figsize=(6, 4))
                magnitud = np.sqrt(jx**2 + jy**2)
                ax_st.streamplot(np.arange(jx.shape[1]), np.arange(jx.shape[0]), jx, jy, density=1.5, color=magnitud, cmap='plasma')
                ax_st.set_title("Líneas de Corriente (Streamlines)")
                st.pyplot(fig_st)
            else:
                st.info("Requiere variables aJx y aJy en los datos actuales.")

        # -----------------------------------------------------------------
        # 4. ESTADÍSTICA Y CORRELACIÓN
        # -----------------------------------------------------------------
        with subtabs[3]:
            st.markdown("Distribuciones globales para todo el dominio simulado.")
            df_dict = {k: v.flatten() for k, v in datos.items() if v.ndim in (2, 3)}
            
            if df_dict:
                df = pd.DataFrame(df_dict)
                ce1, ce2, ce3 = st.columns(3)
                
                with ce1:
                    var_hist = st.selectbox("Variable distribuciones:", list(df.columns), key="v_hist")
                    fig_h = px.histogram(df, x=var_hist, marginal="box", title=f"Histograma ({var_hist})")
                    st.plotly_chart(fig_h, use_container_width=True)
                with ce2:
                    fig_v = px.violin(df, y=var_hist, box=True, title=f"Violín ({var_hist})")
                    st.plotly_chart(fig_v, use_container_width=True)
                with ce3:
                    st.markdown("**Matriz de Correlación**")
                    fig_c = px.imshow(df.corr(), text_auto=".2f", color_continuous_scale="RdBu_r")
                    st.plotly_chart(fig_c, use_container_width=True)

                st.markdown("### Relaciones Multivariables")
                cm1, cm2 = st.columns(2)
                df_samp = df.sample(n=min(3000, len(df)), random_state=42)
                
                with cm1:
                    vx = st.selectbox("Eje X (Dispersión):", list(df.columns), index=0)
                    vy = st.selectbox("Eje Y (Dispersión):", list(df.columns), index=min(1, len(df.columns)-1))
                    fig_j = px.scatter(df_samp, x=vx, y=vy, marginal_x="histogram", marginal_y="histogram", opacity=0.4)
                    st.plotly_chart(fig_j, use_container_width=True)
                with cm2:
                    vp = st.multiselect("Coordenadas Paralelas:", list(df.columns), default=list(df.columns)[:4])
                    if len(vp) > 1:
                        fig_p = px.parallel_coordinates(df_samp, dimensions=vp, color=vp[0], color_continuous_scale=px.colors.diverging.Tealrose)
                        st.plotly_chart(fig_p, use_container_width=True)

        # -----------------------------------------------------------------
        # 5. RECONSTRUCCIÓN 3D INTERACTIVA
        # -----------------------------------------------------------------
        with subtabs[4]:
            st.markdown("Visualización volumétrica (Requiere modelo 3D y variable de densidad de pares).")
            if es_3d and ("d4" in datos or "d" in datos):
                var_vol = "d4" if "d4" in datos else "d"
                vol_data = datos[var_vol]
                X, Y, Z = np.mgrid[0:vol_data.shape[0], 0:vol_data.shape[1], 0:vol_data.shape[2]]
                
                fig_3d = go.Figure(data=go.Isosurface(
                    x=X.flatten(), y=Y.flatten(), z=Z.flatten(),
                    value=vol_data.flatten(),
                    isomin=0.1, isomax=0.9, surface_count=4,
                    colorscale="Viridis", caps=dict(x_show=False, y_show=False)
                ))
                fig_3d.update_layout(
                    scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'), 
                    title=f"Isosuperficies 3D (Tubos de flujo para {var_vol})",
                    margin=dict(l=0, r=0, b=0, t=30)
                )
                st.plotly_chart(fig_3d, use_container_width=True)
            else:
                st.info("La simulación actual no es 3D o carece de la variable de densidad requerida.")


if __name__ == "__main__":
    main()