function estado = solver_tdgl_2d(estado, H_actual, cfg)
% SOLVER_TDGL_2D Evoluciona las ecuaciones TDGL para el modelo de 2 bandas.

    % 1. Desempaquetar constantes y dimensiones
    Nx = estado.Nx; Ny = estado.Ny;
    rx = estado.rx; ry = estado.ry;
    dt = estado.dt; T = cfg.T; Gap = cfg.Gap;
    txy = estado.txy; tyx = estado.tyx; dxdy = estado.dxdy;

    % 2. Desempaquetar matrices físicas
    G = estado.G; G2 = estado.G2;
    F = estado.F; F3 = estado.F3;
    thetax = estado.thetax; thetay = estado.thetay;
    phix = estado.phix; phiy = estado.phiy;
    Ux = estado.Ux; Uy = estado.Uy;
    Vx = estado.Vx; Vy = estado.Vy;
    Qx = estado.Qx; Qy = estado.Qy;
    hz = estado.hz;
    phase = estado.phase; phase3 = estado.phase3;

    % Inicializar memoria de convergencia
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

    ix = 2:Nx;
    iy = 2:Ny;

    % 3. Bucle principal de relajación temporal
    while m <= mMax
        l = 1;
        while l <= lMax
            % --- A. Parámetro de Orden Banda 1 ---
            F(ix, iy) = G(ix, iy) ...
                + rx .* (Vx(ix, iy) .* G(ix+1, iy) - 2.*G(ix, iy) + conj(Vx(ix-1, iy)) .* G(ix-1, iy)) ...
                + ry .* (Vy(ix, iy) .* G(ix, iy+1) - 2.*G(ix, iy) + conj(Vy(ix, iy-1)) .* G(ix, iy-1)) ...
                + (dt .* (1 - T)) .* G(ix, iy) .* (1 - abs(G(ix, iy)).^2) ...
                + Gap .* abs(G2(ix, iy)) .* sin(phase3(ix, iy));

            % --- B. Parámetro de Orden Banda 2 ---
            F3(ix, iy) = G2(ix, iy) ...
                + rx .* (Vx(ix, iy) .* G2(ix+1, iy) - 2.*G2(ix, iy) + conj(Vx(ix-1, iy)) .* G2(ix-1, iy)) ...
                + ry .* (Vy(ix, iy) .* G2(ix, iy+1) - 2.*G2(ix, iy) + conj(Vy(ix, iy-1)) .* G2(ix, iy-1)) ...
                + (dt .* (1 - T)) .* G2(ix, iy) .* (1 - abs(G2(ix, iy)).^2) ...
                - Gap .* abs(G(ix, iy)) .* sin(phase(ix, iy));

            % --- C. Supercorrientes y Potencial Vector en X ---
            Qx(1:Nx, iy) = imag(conj(G(1:Nx, iy)) .* Vx(1:Nx, iy) .* G(2:Nx+1, iy)) ...
                         + Gap .* imag(conj(G2(1:Nx, iy)) .* Vx(1:Nx, iy) .* G2(2:Nx+1, iy));
            
            phix(1:Nx, iy) = thetax(1:Nx, iy) + ((1 - T) .* dt) .* Qx(1:Nx, iy) ...
                           - txy .* (hz(1:Nx, iy) - hz(1:Nx, iy-1));
            Ux(1:Nx, iy) = exp(-1i .* phix(1:Nx, iy));

            % --- D. Supercorrientes y Potencial Vector en Y ---
            Qy(ix, 1:Ny) = imag(conj(G(ix, 1:Ny)) .* Vy(ix, 1:Ny) .* G(ix, 2:Ny+1)) ...
                         + Gap .* imag(conj(G2(ix, 1:Ny)) .* Vy(ix, 1:Ny) .* G2(ix, 2:Ny+1));
            
            phiy(ix, 1:Ny) = thetay(ix, 1:Ny) + ((1 - T) .* dt) .* Qy(ix, 1:Ny) ...
                           + tyx .* (hz(ix, 1:Ny) - hz(ix-1, 1:Ny));
            Uy(ix, 1:Ny) = exp(-1i .* phiy(ix, 1:Ny));

            % --- E. Campo Magnético Local B = rot(A) ---
            hz(2:Nx-1, 2:Ny-1) = (phiy(3:Nx, 2:Ny-1) - phiy(2:Nx-1, 2:Ny-1) ...
                                - phix(2:Nx-1, 3:Ny) + phix(2:Nx-1, 2:Ny-1)) ./ dxdy;

            % --- F. Condiciones de Contorno Banda 1 ---
            F(1, iy)     = Ux(1, iy) .* F(2, iy);
            F(Nx+1, iy)  = conj(Ux(Nx, iy)) .* F(Nx, iy);
            F(ix, 1)     = Uy(ix, 1) .* F(ix, 2);
            F(ix, Ny+1)  = conj(Uy(ix, Ny)) .* F(ix, Ny);

            % --- G. Condiciones de Contorno Banda 2 ---
            F3(1, iy)    = Ux(1, iy) .* F3(2, iy);
            F3(Nx+1, iy) = conj(Ux(Nx, iy)) .* F3(Nx, iy);
            F3(ix, 1)    = Uy(ix, 1) .* F3(ix, 2);
            F3(ix, Ny+1) = conj(Uy(ix, Ny)) .* F3(ix, Ny);

            % --- H. Condiciones de Contorno Campo Magnético Externo ---
            hz(1, 1:Ny)      = H_actual;
            hz(Nx, 1:Ny)     = H_actual;
            hz(2:Nx-1, 1)    = H_actual;
            hz(2:Nx-1, Ny)   = H_actual;

            % --- I. Actualización para el siguiente sub-paso ---
            G = F; G2 = F3;
            thetax = phix; thetay = phiy;
            Vx = Ux; Vy = Uy;

            l = l + 1;
        end

        % --- J. Suavizado en Esquinas ---
        F(1, 1)       = 0.5 .* (F(2, 1) + F(1, 2));
        F(1, Ny+1)    = 0.5 .* (F(1, Ny) + F(2, Ny+1));
        F(Nx+1, 1)    = 0.5 .* (F(Nx, 1) + F(Nx+1, 2));
        F(Nx+1, Ny+1) = 0.5 .* (F(Nx, Ny+1) + F(Nx+1, Ny));

        F3(1, 1)       = 0.5 .* (F3(2, 1) + F3(1, 2));
        F3(1, Ny+1)    = 0.5 .* (F3(1, Ny) + F3(2, Ny+1));
        F3(Nx+1, 1)    = 0.5 .* (F3(Nx, 1) + F3(Nx+1, 2));
        F3(Nx+1, Ny+1) = 0.5 .* (F3(Nx, Ny+1) + F3(Nx+1, Ny));

        % --- K. Criterio de Convergencia Vectorizado ---
        Cooper1 = abs(F);
        diff = max(abs(Cooper1(:) - Cooper0(:)));
        Cooper0 = Cooper1;

        diffh = max(abs(hz(:) - fieldOld(:)));
        fieldOld = hz;

        % Monitor de progreso en terminal
        if mod(m, 500) == 0
            fprintf('   [H = %.2f | Iter: %d] diff_psi = %.2e, diff_hz = %.2e\n', ...
                    H_actual, m * lMax, diff, diffh);
            fflush(stdout);
        end

        if (diff < cfg.eps) && (diffh < cfg.eps)
            break;
        end

        m = m + 1;
    end

    % --- L. Actualización de fase para exportación o paso siguiente ---
    phase  = imag(log(F));
    phase3 = imag(log(F3));

    % 4. Empaquetar matrices actualizadas en el estado
    estado.G = G; estado.G2 = G2;
    estado.F = F; estado.F3 = F3;
    estado.thetax = thetax; estado.thetay = thetay;
    estado.phix = phix; estado.phiy = phiy;
    estado.Ux = Ux; estado.Uy = Uy;
    estado.Vx = Vx; estado.Vy = Vy;
    estado.Qx = Qx; estado.Qy = Qy;
    estado.hz = hz;
    estado.phase = phase; estado.phase3 = phase3;
    estado.Cooper0 = Cooper0; estado.fieldOld = fieldOld;
    estado.iteraciones = m * lMax;
end