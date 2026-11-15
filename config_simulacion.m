function cfg = config_simulacion()
% CONFIG_SIMULACION Define todos los parámetros físicos, geométricos y numéricos.
% Permite seleccionar entre el modelo 2D (2 bandas) y 3D (1 banda), así como
% activar variantes de condiciones de contorno y optimizaciones.

    %% 1. SELECCIÓN DE MODELO Y VARIANTES FÍSICAS
    cfg.modelo = '3D_1Banda';           % Opciones: '2D_2Bandas' | '3D_1Banda'
    
    % Variantes exclusivas para 3D (rescatando el código comentado original)
    cfg.geometria_tau = 'bloque';       % Opciones: 'bloque' (activo) | 'estricto' (enlaces interiores)
    cfg.suavizado_bordes = '8_vertices';% Opciones: '8_vertices' (activo) | '12_aristas' (comentado) | 'ambos'

    %% 2. PARÁMETROS GEOMÉTRICOS Y DE MALLA
    cfg.dx = 0.25;
    cfg.dy = 0.25;
    cfg.dz = 0.25;                      % Solo usado en 3D
    
    % Caja externa (todo el dominio)
    cfg.a = 10;                         % Usar 10 para replicar TDGL2B original 20 en 3D
    cfg.b = 10;                         % Usar 10 para replicar TDGL2B original 20 en 3D
    cfg.c = 10;                         % Solo usado en 3D
    
    % Caja interna (muestra superconductora en 3D)
    cfg.aa = 10;
    cfg.bb = 10;
    cfg.cc = 5;

    %% 3. PARÁMETROS FÍSICOS DEL SUPERCONDUCTOR
    cfg.kappa = 1.0;                    % Parámetro de Ginzburg-Landau (k)
    cfg.bt = 1.0;                       % Coeficiente de relajación
    cfg.T = 0.0;                        % Temperatura reducida (T/Tc)
    cfg.Gap = -0.001;                   % Acoplamiento interbanda (solo 2D_2Bandas)

    %% 4. BARRIDO DE CAMPO MAGNÉTICO EXTERNO
    cfg.Hi = 0.0;
    cfg.Hf = 0.1; %2.0
    cfg.dH = 0.1;

    %% 5. CONTROL NUMÉRICO Y OPTIMIZACIÓN
    cfg.eps = 1e-5;                     % Tolerancia de convergencia (1e-5 en 2D, 1e-7 en 3D)
    cfg.nMax = 10000000;                % Máximo total de iteraciones temporales
    cfg.lMax = 100;                     % Sub-iteraciones internas antes de verificar convergencia
    cfg.is_restart = false;             % false: iniciar desde cero | true: cargar restart/

    %% 6. SALIDA Y VISUALIZACIÓN
    cfg.output_dir = 'output_modular';  % Carpeta separada para no sobrescribir tus resultados base
    cfg.graficar_en_vivo = false;       % false acelera drásticamente el cómputo
    cfg.guardar_campos_extra = false;   % true crea carpetas efieldx/efieldy en 2D
end