function obs = calcular_observables(estado, H_actual, cfg)
% CALCULAR_OBSERVABLES Calcula magnetización, energías de Ginzburg-Landau y 
% matrices de salida de forma 100% vectorizada (sin bucles for).

    if strcmp(cfg.modelo, '3D_1Banda')
        Nx = estado.Nx; Ny = estado.Ny; Nz = estado.Nz;
        x1 = estado.x1; x2 = estado.x2;
        y1 = estado.y1; y2 = estado.y2;
        z1 = estado.z1; z2 = estado.z2;
        jxjyjz = estado.jxjyjz;

        F = estado.F;
        Ux = estado.Ux; Uy = estado.Uy; Uz = estado.Uz;
        Qx = estado.Qx; Qy = estado.Qy;
        hx = estado.hx; hy = estado.hy; hz = estado.hz;

        % 1. Constantes de normalización
        CenergyC  = (1 - cfg.T) / jxjyjz;
        CenergyCd = (1 - cfg.T)^2 / jxjyjz;
        CenergyF  = cfg.kappa^2 / jxjyjz;

        % 2. Observables de campo y fase
        obs.d  = log(abs(F));
        obs.d2 = F;
        obs.d3 = abs(F).^2;
        obs.d4 = abs(F);
        obs.phase = imag(log(F));

        obs.aJx = zeros(Nx, Ny, Nz);
        obs.aJy = zeros(Nx, Ny, Nz);
        obs.aJx(1:Nx, 1:Ny, 2:Nz) = 0.5 .* estado.currentx .* (Qx(1:Nx, 1:Ny, 2:Nz) + Qx(1:Nx, 2:Ny+1, 2:Nz));
        obs.aJy(1:Nx, 1:Ny, 2:Nz) = 0.5 .* estado.currenty .* (Qy(1:Nx, 1:Ny, 2:Nz) + Qy(2:Nx+1, 1:Ny, 2:Nz));

        % 3. Flujo Magnético y Magnetización (Vectorizado sobre x1:x2, y1:y2, z1:z2)
        hz_mag = hz(x1:x2, y1:y2, z1:z2);
        fluxNew = sum(hz_mag(:));
        obs.Bz = fluxNew / jxjyjz;
        obs.M  = H_actual - obs.Bz;

        % 4. Energía Cinética (Vectorizada sobre x1+1:x2, y1+1:y2, z1+1:z2)
        ix = x1+1:x2; iy = y1+1:y2; iz = z1+1:z2;
        grad_x = abs(Ux(ix, iy, iz) .* obs.d2(ix+1, iy, iz) - obs.d2(ix, iy, iz)) ./ cfg.dx;
        grad_y = abs(Uy(ix, iy, iz) .* obs.d2(ix, iy+1, iz) - obs.d2(ix, iy, iz)) ./ cfg.dy;
        grad_z = abs(Uz(ix, iy, iz) .* obs.d2(ix, iy, iz+1) - obs.d2(ix, iy, iz)) ./ cfg.dz;
        obs.E_cin = CenergyC * sum(grad_x(:).^2 + grad_y(:).^2 + grad_z(:).^2);

        % 5. Energía de Condensación (Vectorizada sobre x1+1:x2, y1+1:y2, z1+1:z2)
        d4_sub = obs.d4(ix, iy, iz);
        obs.E_cond = CenergyCd * sum(d4_sub(:) .* (0.5 .* d4_sub(:) - 1.0));

        % 6. Energía de Campo Magnético (Vectorizada sobre x1:x2, y1:y2, z1:z2)
        hz_diff = hz(x1:x2, y1:y2, z1:z2) - H_actual;
        hy_sub  = hy(x1:x2, y1:y2, z1:z2);
        hx_sub  = hx(x1:x2, y1:y2, z1:z2);
        obs.E_campo = CenergyF * sum(hz_diff(:).^2 + hy_sub(:).^2 + hx_sub(:).^2);

        % Energía Libre Total
        obs.E_tot = obs.E_campo + obs.E_cin + obs.E_cond;

    elseif strcmp(cfg.modelo, '2D_2Bandas')
        Nx = estado.Nx; Ny = estado.Ny;
        NxNy = Nx * Ny;
        F = estado.F; F3 = estado.F3;
        Ux = estado.Ux; Uy = estado.Uy;
        hz = estado.hz;

        % Observables 2D (2 Bandas)
        obs.d  = abs(F);
        obs.d5 = F;
        obs.d3 = abs(F).^2;
        obs.d2 = abs(log(F));
        obs.B  = abs(F3);
        obs.phase  = imag(log(F));
        obs.phase3 = imag(log(F3));

        % Magnetización 2D
        hz_sub = hz(1:Nx, 1:Ny);
        obs.Bz = sum(hz_sub(:)) / NxNy;
        obs.M  = H_actual - obs.Bz;

        % Energías 2D (manteniendo las constantes exactas de TDGL2B.m)
        ix = 2:Nx; iy = 2:Ny;
        grad_x = abs(Ux(ix, iy) .* obs.d5(ix+1, iy) - obs.d5(ix, iy)) ./ Nx;
        grad_y = abs(Uy(ix, iy) .* obs.d5(ix, iy+1) - obs.d5(ix, iy)) ./ Ny;
        obs.E_cin = sum(grad_x(:).^2 + grad_y(:).^2);

        d3_sub = obs.d3(ix, iy);
        obs.E_cond = ((1 - cfg.T)^2 / Nx * Ny) * sum(d3_sub(:) .* (0.5 .* d3_sub(:) - 1.0));

        CenergyF = (cfg.kappa^2 / Nx) * Ny;
        hz_diff = hz(1:Nx, 1:Ny) - H_actual;
        obs.E_campo = CenergyF * sum(hz_diff(:).^2);

        obs.E_tot = obs.E_cin + obs.E_cond + obs.E_campo;
    end
end

