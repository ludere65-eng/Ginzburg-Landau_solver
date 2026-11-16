function guardar_restart(estado, p, cfg)
% GUARDAR_RESTART Guarda el estado actual para reinicio de emergencia.
    restart_dir = fullfile(cfg.output_dir, 'restart');
    if ~exist(restart_dir, 'dir')
        mkdir(restart_dir);
    end

    G = estado.G; Ux = estado.Ux; Uy = estado.Uy;
    thetax = estado.thetax; thetay = estado.thetay; hz = estado.hz;

    save(fullfile(restart_dir, 'G.mat'), 'G', '-v7');
    save(fullfile(restart_dir, 'Ux.mat'), 'Ux', '-v7');
    save(fullfile(restart_dir, 'Uy.mat'), 'Uy', '-v7');
    save(fullfile(restart_dir, 'thetax.mat'), 'thetax', '-v7');
    save(fullfile(restart_dir, 'thetay.mat'), 'thetay', '-v7');
    save(fullfile(restart_dir, 'hz.mat'), 'hz', '-v7');
    save(fullfile(restart_dir, 'p.mat'), 'p', '-v7');

    if strcmp(cfg.modelo, '3D_1Banda')
        Uz = estado.Uz; thetaz = estado.thetaz;
        save(fullfile(restart_dir, 'Uz.mat'), 'Uz', '-v7');
        save(fullfile(restart_dir, 'thetaz.mat'), 'thetaz', '-v7');
    end
end
