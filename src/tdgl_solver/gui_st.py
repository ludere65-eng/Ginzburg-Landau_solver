"""
Interfaz web interactiva en Streamlit para simular (con detección de caché)
y visualizar/animar resultados TDGL en 2D (2 bandas) y 3D (1 banda).
"""
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import seaborn as sns
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
        st.sidebar.header("1. Fuente de Datos")
        # ... (Carga de datos y slider de H igual que antes) ...
        
        # Sub-pestañas para organizar la densidad de información
        subtab_mapas, subtab_vectores, subtab_estadistica, subtab_3d = st.tabs([
            "🗺️ Mapas y Contornos", 
            "↗️ Campos Vectoriales", 
            "📈 Estadística y Distribuciones", 
            "🧊 Reconstrucción 3D"
        ])
        
        datos = loader.cargar_paso_campo(h_seleccionado)
        
        # ---------------------------------------------------------
        # 1. MAPAS INTERACTIVOS Y CONTORNOS (Plotly)
        # ---------------------------------------------------------
        with subtab_mapas:
            st.markdown("Gráficos interactivos con hover, zoom y paneo.")
            col1, col2 = st.columns(2)
            
            if "d4" in datos:
                vista_d4 = datos["d4"][:, :, z_slice] if es_3d else datos["d4"]
                fig_contorno = go.Figure(data=go.Contour(
                    z=vista_d4, colorscale="Viridis", contours=dict(showlines=False)
                ))
                fig_contorno.update_layout(title="Contorno Suavizado: Densidad de Pares (d4)")
                col1.plotly_chart(fig_contorno, use_container_width=True)
                
            if "hz" in datos:
                vista_hz = datos["hz"][:, :, z_slice] if es_3d else datos["hz"]
                fig_calor = px.imshow(vista_hz, color_continuous_scale="RdBu_r", title="Mapa de Calor: Campo Magnético (hz)")
                col2.plotly_chart(fig_calor, use_container_width=True)

        # ---------------------------------------------------------
        # 2. CAMPOS VECTORIALES Y STREAMLINES
        # ---------------------------------------------------------
        with subtab_vectores:
            st.markdown("Análisis del flujo de supercorrientes (aJx, aJy).")
            if "aJx" in datos and "aJy" in datos:
                jx = datos["aJx"][:, :, z_slice] if es_3d else datos["aJx"]
                jy = datos["aJy"][:, :, z_slice] if es_3d else datos["aJy"]
                
                # Crear malla de coordenadas (reduciendo densidad para visibilidad)
                x, y = np.meshgrid(np.arange(0, jx.shape[1], 2), np.arange(0, jx.shape[0], 2))
                u = jx[::2, ::2]
                v = jy[::2, ::2]
                
                fig_quiver = ff.create_quiver(x, y, u, v, scale=0.5, arrow_scale=0.3, name='Corriente', line_color='crimson')
                fig_quiver.update_layout(title="Quiver Plot (Vectores de Corriente J)", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_quiver, use_container_width=True)
                
                # Líneas de corriente (Streamlines) usando Matplotlib empaquetado en Streamlit
                fig_stream, ax = plt.subplots(figsize=(6, 4))
                ax.streamplot(np.arange(jx.shape[1]), np.arange(jx.shape[0]), jx, jy, density=1.5, color=np.sqrt(jx**2 + jy**2), cmap='plasma')
                ax.set_title("Streamlines de Supercorrientes")
                st.pyplot(fig_stream)

        # ---------------------------------------------------------
        # 3. ESTADÍSTICA, DISTRIBUCIONES Y CORRELACIÓN
        # ---------------------------------------------------------
        with subtab_estadistica:
            st.markdown("Análisis global de las variables en todo el dominio espacial.")
            
            # Aplanar matrices y crear un DataFrame tabular para análisis estadístico
            df_dict = {}
            for var_key, matriz in datos.items():
                if matriz.ndim in (2, 3):
                    df_dict[var_key] = matriz.flatten()
            
            if df_dict:
                df = pd.DataFrame(df_dict)
                
                c_est1, c_est2, c_est3 = st.columns(3)
                
                with c_est1:
                    var_hist = st.selectbox("Variable para Histograma/Violín:", list(df.columns), key="hist_var")
                    fig_hist = px.histogram(df, x=var_hist, marginal="box", title=f"Distribución y Caja de {var_hist}")
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                with c_est2:
                    fig_violin = px.violin(df, y=var_hist, box=True, points="all", title=f"Violin Plot: {var_hist}")
                    st.plotly_chart(fig_violin, use_container_width=True)
                    
                with c_est3:
                    st.markdown("**Matriz de Correlación**")
                    corr_matrix = df.corr()
                    fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r")
                    st.plotly_chart(fig_corr, use_container_width=True)
                
                # Jointplot (Dispersión Marginal) y Coordenadas Paralelas
                st.markdown("### Relaciones Multivariables")
                col_m1, col_m2 = st.columns(2)
                
                with col_m1:
                    var_x = st.selectbox("Eje X (Dispersión):", list(df.columns), index=0)
                    var_y = st.selectbox("Eje Y (Dispersión):", list(df.columns), index=min(1, len(df.columns)-1))
                    # Muestreo para no saturar el navegador con millones de puntos
                    df_sample = df.sample(n=min(5000, len(df))) 
                    fig_joint = px.scatter(df_sample, x=var_x, y=var_y, marginal_x="histogram", marginal_y="histogram", opacity=0.3)
                    st.plotly_chart(fig_joint, use_container_width=True)
                    
                with col_m2:
                    vars_paralelas = st.multiselect("Variables para Coordenadas Paralelas:", list(df.columns), default=list(df.columns)[:4])
                    if len(vars_paralelas) > 1:
                        fig_parcoords = px.parallel_coordinates(df_sample, dimensions=vars_paralelas, color=vars_paralelas[0], color_continuous_scale=px.colors.diverging.Tealrose)
                        st.plotly_chart(fig_parcoords, use_container_width=True)

        # ---------------------------------------------------------
        # 4. RECONSTRUCCIÓN 3D INTERACTIVA
        # ---------------------------------------------------------
        with subtab_3d:
            if es_3d and "d4" in datos:
                st.markdown("Isosuperficies tridimensionales con rotación y zoom en tiempo real.")
                vol_data = datos["d4"]
                X, Y, Z = np.mgrid[0:vol_data.shape[0], 0:vol_data.shape[1], 0:vol_data.shape[2]]
                
                fig_3d = go.Figure(data=go.Isosurface(
                    x=X.flatten(),
                    y=Y.flatten(),
                    z=Z.flatten(),
                    value=vol_data.flatten(),
                    isomin=0.1,
                    isomax=0.9,
                    surface_count=5, # Número de capas de contorno 3D
                    colorscale="Viridis",
                    caps=dict(x_show=False, y_show=False)
                ))
                fig_3d.update_layout(scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'), title="Vórtices 3D (Tubos de flujo)")
                st.plotly_chart(fig_3d, use_container_width=True)
            else:
                st.info("La reconstrucción 3D requiere que el modelo actual sea 3D_1Banda y contenga la variable de densidad de pares.")

if __name__ == "__main__":
    main()