# TDGL Solver

Un paquete integral en Python para la simulación numérica y análisis avanzado de ecuaciones dependientes del tiempo de Ginzburg-Landau (TDGL). Diseñado para estudiar la dinámica de vórtices y skyrmiones en sistemas superconductores de múltiples bandas.

## Características Principales

* **Motor Numérico Híbrido:** Núcleo de cálculo modularizado en GNU Octave encapsulado mediante un orquestador en Python.
* **Modelos Soportados:**
  * **2D de Dos Bandas:** Acoplamiento interbanda (`Gap`) para densidades fraccionarias.
  * **3D de Una Banda:** Entornos de caja interna/externa con geometrías configurables (`tau`) y suavizado de bordes.
* **Sistema de Caché Inteligente:** Detección de huella digital (SHA-256) de parámetros que evita recalcular configuraciones ya simuladas.
* **Interfaces Gráficas de Usuario (GUIs):**
  * **Escritorio (Tkinter):** Monitor de progreso en tiempo real y ejecución asíncrona.
  * **Web/Dashboard (Streamlit):** Análisis multivariable con Plotly, correlaciones estadísticas (Pandas/Seaborn), streamlines vectoriales y reconstrucción de vórtices 3D.

## Requisitos Previos

1. **GNU Octave:** El motor requiere que GNU Octave esté instalado y disponible en las variables de entorno del sistema (`PATH`).
   * **Linux (Debian/Ubuntu):** `sudo apt install octave`
   * **Windows:** Descargar desde [gnu.org/software/octave](https://gnu.org/software/octave) y agregar a la ruta (`PATH`).
2. **Python 3.9+**

## Instalación

Clona el repositorio e instala el paquete con todas sus dependencias en modo editable:

```bash
git clone https://github.com/ludere65-eng/Ginzburg-Landau_solver.git
cd Ginzburg-Landau_solver
pip install -e .
```

Para instalar también las herramientas de generación de documentación:

```bash
pip install -e ".[docs]"
```

## Uso

Una vez instalado, tienes dos formas de lanzar la suite de herramientas:

### 1. Interfaz Web Analítica (Streamlit)
Ideal para análisis de datos interactivos, visualización 3D y gráficos estadísticos:
```bash
streamlit run src/tdgl_solver/gui_st.py
```

### 2. Interfaz de Escritorio (Tkinter)
Ligera y nativa, ideal para lanzar simulaciones rápidamente de forma local:
```bash
tdgl-tk
```

## Documentación

Para generar y visualizar la documentación técnica localmente con MkDocs:

```bash
mkdocs serve
```

Para desplegarla directamente en GitHub Pages:

```bash
mkdocs gh-deploy
```

## Estructura del Proyecto

Los resultados de las simulaciones se guardan automáticamente en la carpeta `runs/` en la raíz del proyecto, clasificados por modelo y un hash único de los parámetros físicos utilizados. Las carpetas `Codigo2/output` y `Codigo3/output` mantienen la compatibilidad con las corridas *legacy*.