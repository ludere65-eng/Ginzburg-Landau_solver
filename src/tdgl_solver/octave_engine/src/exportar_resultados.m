function exportar_resultados(estado, obs, H_actual, cfg)
% EXPORTAR_RESULTADOS Crea las carpetas por campo H y exporta los archivos .mat
% manteniendo exactamente el mismo formato que Codigo2 y Codigo3 originales.

    dir_H = num2str(H_actual);
    base = cfg.output_dir;

    % Carpetas comunes a 2D y 3D
    carpetas = {'psi', 'field', 'phase'};
    if strcmp(cfg.modelo, '3D_1Banda')
        carpetas = [carpetas, {'currentsx', 'currentsy'}];
    elseif strcmp(cfg.modelo, '2D_2Bandas') && cfg.guardar_campos_extra
        carpetas = [carpetas, {'efieldx', 'efieldy'}];
    end

    for k = 1:length(carpetas)
        ruta = fullfile(base, carpetas{k}, dir_H);
        if ~exist(ruta, 'dir')
            mkdir(ruta);
        end
    end

    % Variables comunes
    d = obs.d;
    hz = estado.hz;
    phase = obs.phase;
    save(fullfile(base, 'psi', dir_H, 'd.mat'), 'd');
    save(fullfile(base, 'field', dir_H, 'hz.mat'), 'hz');
    save(fullfile(base, 'phase', dir_H, 'phase.mat'), 'phase');

    % Variables específicas de cada dimensión
    if strcmp(cfg.modelo, '3D_1Banda')
        d4 = obs.d4;
        aJx = obs.aJx;
        aJy = obs.aJy;
        save(fullfile(base, 'psi', dir_H, 'd4.mat'), 'd4');
        save(fullfile(base, 'currentsx', dir_H, 'aJx.mat'), 'aJx');
        save(fullfile(base, 'currentsy', dir_H, 'aJy.mat'), 'aJy');
    elseif strcmp(cfg.modelo, '2D_2Bandas')
        B = obs.B;
        d2 = obs.d2;
        save(fullfile(base, 'psi', dir_H, 'B.mat'), 'B');
        save(fullfile(base, 'psi', dir_H, 'd2.mat'), 'd2');
    end
end