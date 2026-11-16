"""
Interfaz web interactiva usando Streamlit para configuración y visualización TDGL.
"""
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from tdgl_solver.io_handler import TDGLDataLoader

# Configuración de la página
st.set_page_config(page_title="TDGL Solver Dashboard", layout="wide")
st.title("Visualización de Resultados TDGL")

# Panel lateral de configuración
st.sidebar.header("Panel de Control")
ruta_datos = st.sidebar.text_input(
    "Directorio de resultados (ruta relativa o absoluta):", 
    value="output_modular"
)

try:
    loader = TDGLDataLoader(ruta_datos)
    campos = loader.listar_campos_disponibles()
    
    if not campos:
        st.warning("No se encontraron resultados en el directorio especificado.")
    else:
        # Controles de selección de datos
        h_seleccionado = st.sidebar.selectbox("Seleccione el Campo Magnético (H):", campos)
        datos = loader.cargar_paso_campo(h_seleccionado)
        
        # Área de visualización principal
        st.write(f"### Analizando estado en H = {h_seleccionado}")
        
        vars_disponibles = list(datos.keys())
        col1, col2 = st.columns([1, 3])
        
        with col1:
            var_plot = st.radio("Variable a visualizar:", vars_disponibles)
        
        with col2:
            if var_plot:
                matriz = datos[var_plot] 
                
                # Manejo automático de matrices 2D y 3D
                if matriz.ndim == 3: ### asdfasdfasdf 
                    z_slice = st.slider(
                        "Corte transversal (Z):", 
                        0, matriz.shape[2] - 1, 
                        matriz.shape[2] // 2
                    )
                    vista = matriz[:, :, z_slice]
                else:
                    vista = matriz
                
                # Renderizado del mapa de color
                fig, ax = plt.subplots(figsize=(8, 6))
                cax = ax.imshow(vista, cmap="viridis", origin="lower")
                fig.colorbar(cax, ax=ax)
                ax.set_title(f"Distribución de {var_plot} (H = {h_seleccionado})")
                ax.set_xlabel("x")
                ax.set_ylabel("y")
                
                st.pyplot(fig)
                
except FileNotFoundError:
    st.error(f"El directorio '{ruta_datos}' no existe. Asegúrate de ejecutar la simulación primero.")