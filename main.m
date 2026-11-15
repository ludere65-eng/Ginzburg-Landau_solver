% MAIN.M - Orquestador Principal para Simulaciones TDGL (2D 2-Bandas y 3D)
format long;
clear; clc;
addpath('src'); % Añade la carpeta de módulos al path de Octave/MATLAB

% 1. Cargar configuración del usuario
cfg = config_simulacion();
fprintf('Iniciando simulación en modo: %s\n', cfg.modelo);
tiempo_total = tic;

% 2. Inicializar mallas, constantes y condiciones iniciales
estado = init_sistema(cfg);

% 3. Bucle principal sobre el barrido de campo magnético H
H_vec = cfg.Hi : cfg.dH : cfg.Hf;
num_H = length(H_vec);

% Pre-asignación de vectores de resultados globales (evita redimensionar en cada paso)
resultados.Mag = zeros(num_H, 2);
resultados.Energia = zeros(num_H, 4); % [H, E_cin, E_cond, E_tot]

for p = 1:num_H
    H_actual = H_vec(p);
    t_paso = tic;
    
    % Guardar checkpoint de reinicio
    guardar_restart(estado, p, cfg);
    
    % 4. Evolución temporal hasta estado estacionario (según modelo elegido)
    if strcmp(cfg.modelo, '3D_1Banda')
        estado = solver_tdgl_3d(estado, H_actual, cfg);
    elseif strcmp(cfg.modelo, '2D_2Bandas')
        estado = solver_tdgl_2d(estado, H_actual, cfg);
    else
        error('Modelo no reconocido en config_simulacion.m');
    end
    
    % 5. Cálculo vectorizado de Energía Libre y Magnetización
    obs = calcular_observables(estado, H_actual, cfg);
    resultados.Mag(p, :) = [H_actual, obs.M];
    resultados.Energia(p, :) = [H_actual, obs.E_cin, obs.E_cond, obs.E_tot];
    
    % 6. Exportar matrices (.mat) del paso actual
    exportar_resultados(estado, obs, H_actual, cfg);
    
    % 7. Gráficas opcionales
    if cfg.graficar_en_vivo
        actualizar_graficas(resultados, p);
    end
    
    fprintf('Campo H = %.2f completado en %.2f s (Iteraciones: %d)\n', ...
            H_actual, toc(t_paso), estado.iteraciones);
end

fprintf('Simulación finalizada en %.2f segundos.\n', toc(tiempo_total));