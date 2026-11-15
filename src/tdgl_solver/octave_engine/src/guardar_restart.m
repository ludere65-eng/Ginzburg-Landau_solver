function guardar_restart(estado, p, cfg)
% GUARDAR_RESTART Guarda el estado actual para reinicio de emergencia.
    restart_dir = fullfile(cfg.output_dir, 'restart');
    if ~exist(restart_dir, 'dir')
        mkdir(restart_dir);
    end

    G = estado.G; Ux = estado.Ux; Uy = estado.Uy;
    thetax = estado.thetax; thetay = estado.thetay; hz = estado.hz;

    save(fullfile(restart_dir, 'G.mat'), 'G');
    save(fullfile(restart_dir, 'Ux.mat'), 'Ux');
    save(fullfile(restart_dir, 'Uy.mat'), 'Uy');
    save(fullfile(restart_dir, 'thetax.mat'), 'thetax');
    save(fullfile(restart_dir, 'thetay.mat'), 'thetay');
    save(fullfile(restart_dir, 'hz.mat'), 'hz');
    save(fullfile(restart_dir, 'p.mat'), 'p');

    if strcmp(cfg.modelo, '3D_1Banda')
        Uz = estado.Uz; thetaz = estado.thetaz;
        save(fullfile(restart_dir, 'Uz.mat'), 'Uz');
        save(fullfile(restart_dir, 'thetaz.mat'), 'thetaz');
    end
end
