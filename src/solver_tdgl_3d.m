function estado = solver_tdgl_3d(estado, H_actual, cfg)
% SOLVER_TDGL_3D Evoluciona las ecuaciones TDGL en 3D hasta el estado estacionario
% para un valor dado de campo magnético externo (H_actual).

    % 1. Desempaquetar dimensiones y constantes (evita overhead en el bucle)
    Nx = estado.Nx; Ny = estado.Ny; Nz = estado.Nz;
    x1 = estado.x1; x2 = estado.x2;
    y1 = estado.y1; y2 = estado.y2;
    z1 = estado.z1; z2 = estado.z2;

    rx = estado.rx; ry = estado.ry; rz = estado.rz;
    c1 = estado.c1; d1 = estado.d1;
    sxy = estado.sxy; sxz = estado.sxz;
    syx = estado.syx; syz = estado.syz;
    szx = estado.szx; szy = estado.szy;

    dxdy = cfg.dx * cfg.dy;
    dydz = cfg.dy * cfg.dz;
    dzdx = cfg.dz * cfg.dx;

    % 2. Desempaquetar matrices físicas
    G = estado.G; F = estado.F;
    taux = estado.taux; tauy = estado.tauy; tauz = estado.tauz;
    thetax = estado.thetax; thetay = estado.thetay; thetaz = estado.thetaz;
    phix = estado.phix; phiy = estado.phiy; phiz = estado.phiz;
    Ux = estado.Ux; Uy = estado.Uy; Uz = estado.Uz;
    Vx = estado.Vx; Vy = estado.Vy; Vz = estado.Vz;
    Qx = estado.Qx; Qy = estado.Qy; Qz = estado.Qz;
    hx = estado.hx; hy = estado.hy; hz = estado.hz;

    % Inicializar memoria de convergencia si es el primer paso de campo H
    if ~isfield(estado, 'Cooper0')
        Cooper0 = abs(G);
        fieldOld = hz;
    else
        Cooper0 = estado.Cooper0;
        fieldOld = estado.fieldOld;
    end

    lMax = cfg.lMax;
    mMax = cfg.nMax / lMax;
    m = 1;

    % Pre-definir rangos de índices de la caja interna para legibilidad y rapidez
    ix = x1+1:x2;
    iy = y1+1:y2;
    iz = z1+1:z2;

    % 3. Bucle de relajación hacia el estado estacionario
    while m <= mMax
        l = 1;
        while l <= lMax
            % --- A. Evolución del Parámetro de Orden (TDGL 3D) ---
            G_in = G(ix, iy, iz);
            F(ix, iy, iz) = G_in ...
                + rx .* (Vx(ix, iy, iz) .* G(ix+1, iy, iz) - 2.0 .* G_in + conj(Vx(ix-1, iy, iz)) .* G(ix-1, iy, iz)) ...
                + ry .* (Vy(ix, iy, iz) .* G(ix, iy+1, iz) - 2.0 .* G_in + conj(Vy(ix, iy-1, iz)) .* G(ix, iy-1, iz)) ...
                + rz .* (Vz(ix, iy, iz) .* G(ix, iy, iz+1) - 2.0 .* G_in + conj(Vz(ix, iy, iz-1)) .* G(ix, iy, iz-1)) ...
                + c1 .* G_in .* (1.0 - abs(G_in).^2);

            % --- B. Supercorriente y Potencial Vector en X ---
            Qx(1:Nx, 2:Ny, 2:Nz) = imag(conj(G(1:Nx, 2:Ny, 2:Nz)) .* Vx(1:Nx, 2:Ny, 2:Nz) .* G(2:Nx+1, 2:Ny, 2:Nz));
            phix(1:Nx, 2:Ny, 2:Nz) = thetax(1:Nx, 2:Ny, 2:Nz) ...
                + d1 .* taux(1:Nx, 2:Ny, 2:Nz) .* Qx(1:Nx, 2:Ny, 2:Nz) ...
                - sxy .* (hz(1:Nx, 2:Ny, 2:Nz) - hz(1:Nx, 1:Ny-1, 2:Nz)) ...
                + sxz .* (hy(1:Nx, 2:Ny, 2:Nz) - hy(1:Nx, 2:Ny, 1:Nz-1));
            Ux(1:Nx, 2:Ny, 2:Nz) = exp(-1i .* phix(1:Nx, 2:Ny, 2:Nz));

            % --- C. Supercorriente y Potencial Vector en Y ---
            Qy(2:Nx, 1:Ny, 2:Nz) = imag(conj(G(2:Nx, 1:Ny, 2:Nz)) .* Vy(2:Nx, 1:Ny, 2:Nz) .* G(2:Nx, 2:Ny+1, 2:Nz));
            phiy(2:Nx, 1:Ny, 2:Nz) = thetay(2:Nx, 1:Ny, 2:Nz) ...
                + d1 .* tauy(2:Nx, 1:Ny, 2:Nz) .* Qy(2:Nx, 1:Ny, 2:Nz) ...
                - syz .* (hx(2:Nx, 1:Ny, 2:Nz) - hx(2:Nx, 1:Ny, 1:Nz-1)) ...
                + syx .* (hz(2:Nx, 1:Ny, 2:Nz) - hz(1:Nx-1, 1:Ny, 2:Nz));
            Uy(2:Nx, 1:Ny, 2:Nz) = exp(-1i .* phiy(2:Nx, 1:Ny, 2:Nz));

            % --- D. Supercorriente y Potencial Vector en Z ---
            Qz(2:Nx, 2:Ny, 1:Nz) = imag(conj(G(2:Nx, 2:Ny, 1:Nz)) .* Vz(2:Nx, 2:Ny, 1:Nz) .* G(2:Nx, 2:Ny, 2:Nz+1));
            phiz(2:Nx, 2:Ny, 1:Nz) = thetaz(2:Nx, 2:Ny, 1:Nz) ...
                + d1 .* tauz(2:Nx, 2:Ny, 1:Nz) .* Qz(2:Nx, 2:Ny, 1:Nz) ...
                - szx .* (hy(2:Nx, 2:Ny, 1:Nz) - hy(1:Nx-1, 2:Ny, 1:Nz)) ...
                + szy .* (hx(2:Nx, 2:Ny, 1:Nz) - hx(2:Nx, 1:Ny-1, 1:Nz));
            Uz(2:Nx, 2:Ny, 1:Nz) = exp(-1i .* phiz(2:Nx, 2:Ny, 1:Nz));

            % --- E. Campo Magnético Local B = rot(A) ---
            hx(2:Nx, 2:Ny-1, 2:Nz-1) = (phiz(2:Nx, 3:Ny, 2:Nz-1) - phiz(2:Nx, 2:Ny-1, 2:Nz-1) ...
                                      - phiy(2:Nx, 2:Ny-1, 3:Nz) + phiy(2:Nx, 2:Ny-1, 2:Nz-1)) / dydz;

            hy(2:Nx-1, 2:Ny, 2:Nz-1) = (phix(2:Nx-1, 2:Ny, 3:Nz) - phix(2:Nx-1, 2:Ny, 2:Nz-1) ...
                                      - phiz(3:Nx, 2:Ny, 2:Nz-1) + phiz(2:Nx-1, 2:Ny, 2:Nz-1)) / dzdx;

            hz(2:Nx-1, 2:Ny-1, 2:Nz) = (phiy(3:Nx, 2:Ny-1, 2:Nz) - phiy(2:Nx-1, 2:Ny-1, 2:Nz) ...
                                      - phix(2:Nx-1, 3:Ny, 2:Nz) + phix(2:Nx-1, 2:Ny-1, 2:Nz)) / dxdy;

            % --- F. Condiciones de Contorno (Caras de la Caja Interna) ---
            F(x1, iy, iz)   = Ux(x1, iy, iz) .* F(x1+1, iy, iz);
            F(x2+1, iy, iz) = conj(Ux(x2, iy, iz)) .* F(x2, iy, iz);

            F(ix, y1, iz)   = Uy(ix, y1, iz) .* F(ix, y1+1, iz);
            F(ix, y2+1, iz) = conj(Uy(ix, y2, iz)) .* F(ix, y2, iz);

            F(ix, iy, z1)   = Uz(ix, iy, z1) .* F(ix, iy, z1+1);
            F(ix, iy, z2+1) = conj(Uz(ix, iy, z2)) .* F(ix, iy, z2);

            % --- G. Condiciones de Contorno del Campo Magnético Externo ---
            hx(1, 1:Ny, 1:Nz)    = 0.0;
            hx(Nx+1, 1:Ny, 1:Nz) = 0.0;
            hx(2:Nx, 1, 1:Nz)    = 0.0;
            hx(2:Nx, Ny, 1:Nz)   = 0.0;
            hx(2:Nx, 2:Ny-1, 1)  = 0.0;
            hx(2:Nx, 2:Ny-1, Nz) = 0.0;

            hy(1:Nx, 1, 1:Nz)    = 0.0;
            hy(1:Nx, Ny+1, 1:Nz) = 0.0;
            hy(1:Nx, 2:Ny, 1)    = 0.0;
            hy(1:Nx, 2:Ny, Nz)   = 0.0;
            hy(1, 2:Ny, 2:Nz-1)  = 0.0;
            hy(Nx, 2:Ny, 2:Nz-1) = 0.0;

            hz(1:Nx, 1:Ny, 1)    = H_actual;
            hz(1:Nx, 1:Ny, Nz)   = H_actual;
            hz(1, 1:Ny, 1:Nz)    = H_actual;
            hz(Nx, 1:Ny, 1:Nz)   = H_actual;
            hz(2:Nx-1, 1, 1:Nz)  = H_actual;
            hz(2:Nx-1, Ny, 1:Nz) = H_actual;

            % --- H. Actualización de variables para el siguiente paso ---
            G(x1:x2+1, y1:y2+1, z1:z2+1) = F(x1:x2+1, y1:y2+1, z1:z2+1);
            thetax = phix; Vx = Ux;
            thetay = phiy; Vy = Uy;
            thetaz = phiz; Vz = Uz;

            l = l + 1;
        end

        % --- I. Suavizado de Bordes (8 vértices, 12 aristas o ambos) ---
        F = aplicar_suavizado_3d(F, estado, cfg);

        % --- J. Criterio de Convergencia VECTORIZADO ---
        Cooper1 = abs(F);
        
        % Extraemos únicamente la sub-malla de la caja interna (x1:x2+1, y1:y2+1, z1:z2+1)
        sub_C1 = Cooper1(x1:x2+1, y1:y2+1, z1:z2+1);
        sub_C0 = Cooper0(x1:x2+1, y1:y2+1, z1:z2+1);
        diff = max(abs(sub_C1(:) - sub_C0(:)));
        Cooper0(x1:x2+1, y1:y2+1, z1:z2+1) = sub_C1;

        % Diferencia máxima en todo el dominio de hz (1:Nx, 1:Ny, 1:Nz+1)
        diffh = max(abs(hz(:) - fieldOld(:)));
        fieldOld = hz;

        if (diff < cfg.eps) && (diffh < cfg.eps)
            break;
        end

        m = m + 1;
    end

    % 4. Empaquetar de vuelta en la estructura estado
    estado.G = G; estado.F = F;
    estado.thetax = thetax; estado.thetay = thetay; estado.thetaz = thetaz;
    estado.phix = phix; estado.phiy = phiy; estado.phiz = phiz;
    estado.Ux = Ux; estado.Uy = Uy; estado.Uz = Uz;
    estado.Vx = Vx; estado.Vy = Vy; estado.Vz = Vz;
    estado.Qx = Qx; estado.Qy = Qy; estado.Qz = Qz;
    estado.hx = hx; estado.hy = hy; estado.hz = hz;
    estado.Cooper0 = Cooper0;
    estado.fieldOld = fieldOld;
    estado.iteraciones = m * lMax;
end