% VALIDAR_VS_ORIGINAL.M
% Compara los resultados de la versión modularizada (output_modular/)
% contra las líneas base originales (Codigo2/output o Codigo3/output).
clear; clc;

%% 1. CONFIGURACIÓN DE LA VALIDACIÓN
modo = '3D_1Banda'; % Opciones: '3D_1Banda' | '2D_2Bandas'

% Define los valores de campo H que quieres comparar (deben existir en ambas carpetas)
H_lista = {'0.1'};  % Ej. {'0.1', '0.2', '0.5'}

%% 2. DEFINICIÓN DE RUTAS Y VARIABLES SEGÚN EL MODO
ruta_mod = fullfile('..', 'output_modular');

if strcmp(modo, '3D_1Banda')
    ruta_orig = fullfile('..', 'Codigo3', 'output');
    variables = {
        'psi',       'd.mat',     'd';
        'psi',       'd4.mat',    'd4';
        'field',     'hz.mat',    'hz';
        'phase',     'phase.mat', 'phase';
        'currentsx', 'aJx.mat',   'aJx';
        'currentsy', 'aJy.mat',   'aJy'
    };
elseif strcmp(modo, '2D_2Bandas')
    ruta_orig = fullfile('..', 'Codigo2', 'output');
    variables = {
        'psi',   'd.mat',     'd';
        'psi',   'B.mat',     'B';
        'psi',   'd2.mat',    'd2';
        'field', 'hz.mat',    'hz';
        'phase', 'phase.mat', 'phase'
    };
else
    error('Modo no válido. Usa ''3D_1Banda'' o ''2D_2Bandas''.');
end

%% 3. EJECUCIÓN DE LA COMPARACIÓN NUMÉRICA
fprintf('=================================================================\n');
fprintf(' INICIANDO VALIDACIÓN NUMÉRICA | MODO: %s\n', modo);
fprintf('=================================================================\n');

tolerancia_aceptable = 1e-12; % Precisión de máquina esperada
todo_ok = true;

for h_idx = 1:length(H_lista)
    H_str = H_lista{h_idx};
    fprintf('\n--- Campo Magnético H = %s ---\n', H_str);
    
    for v_idx = 1:size(variables, 1)
        subcarpeta = variables{v_idx, 1};
        archivo    = variables{v_idx, 2};
        var_name   = variables{v_idx, 3};
        
        file_orig = fullfile(ruta_orig, subcarpeta, H_str, archivo);
        file_mod  = fullfile(ruta_mod,  subcarpeta, H_str, archivo);
        
        if ~exist(file_orig, 'file')
            fprintf('  [OMITIDO] No existe original: %s\n', file_orig);
            continue;
        end
        if ~exist(file_mod, 'file')
            fprintf('  [OMITIDO] No existe modular:  %s\n', file_mod);
            continue;
        end
        
        % Cargar estructuras y extraer matrices
        data_orig = load(file_orig);
        data_mod  = load(file_mod);
        
        mat_orig = data_orig.(var_name);
        mat_mod  = data_mod.(var_name);
        
        % Verificar dimensiones
        if ~isequal(size(mat_orig), size(mat_mod))
            fprintf('  [ERROR] %-6s -> Dimensiones distintas: [%s] vs [%s]\n', ...
                    var_name, num2str(size(mat_orig)), num2str(size(mat_mod)));
            todo_ok = false;
            continue;
        end
        
        % Calcular error máximo absoluto y error relativo
        diff_abs = abs(mat_orig(:) - mat_mod(:));
        err_max  = max(diff_abs);
        norma_orig = max(abs(mat_orig(:)));
        
        if norma_orig > 0
            err_rel = err_max / norma_orig;
        else
            err_rel = err_max;
        end
        
        if err_max <= tolerancia_aceptable
            estado_str = 'OK';
        else
            estado_str = 'REVISAR';
            todo_ok = false;
        end
        
        fprintf('  [%-7s] Variable %-6s | Err Abs Max: %.3e | Err Rel: %.3e\n', ...
                estado_str, var_name, err_max, err_rel);
    end
end

fprintf('\n=================================================================\n');
if todo_ok
    fprintf(' RESULTADO FINAL: VALIDACIÓN EXITOSA (Fidelidad numérica verificada)\n');
else
    fprintf(' RESULTADO FINAL: SE DETECTARON DIFERENCIAS (Revisar parámetros)\n');
end
fprintf('=================================================================\n');