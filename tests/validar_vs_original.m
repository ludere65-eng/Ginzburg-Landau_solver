% VALIDAR_VS_ORIGINAL.M
% Compara los resultados de la versión modularizada contra la línea base original (Codigo3)
clear; clc;

H_test = '0.1';
ruta_orig = fullfile('..', 'Codigo3', 'output');
ruta_mod  = fullfile('..', 'output_modular');

archivos = {
    fullfile('psi', H_test, 'd.mat'), 'd';
    fullfile('psi', H_test, 'd4.mat'), 'd4';
    fullfile('field', H_test, 'hz.mat'), 'hz';
    fullfile('phase', H_test, 'phase.mat'), 'phase';
    fullfile('currentsx', H_test, 'aJx.mat'), 'aJx';
    fullfile('currentsy', H_test, 'aJy.mat'), 'aJy'
};

fprintf('=== VALIDACIÓN NUMÉRICA PARA H = %s ===\n', H_test);
for i = 1:size(archivos, 1)
    rel_path = archivos{i, 1};
    var_name = archivos{i, 2};
    
    orig = load(fullfile(ruta_orig, rel_path));
    mod  = load(fullfile(ruta_mod, rel_path));
    
    mat_orig = orig.(var_name);
    mat_mod  = mod.(var_name);
    
    error_max = max(abs(mat_orig(:) - mat_mod(:)));
    fprintf('Variable %-6s -> Error máximo absoluto: %.3e\n', var_name, error_max);
end