function estado = init_sistema(cfg)
% INIT_SISTEMA Inicializa mallas, parámetros y condiciones iniciales.
% Integra la inicialización vectorizada (sin bucles for) y rescata 
% las dos variantes de geometría para 'tau' (bloque vs estricto).

    % 1. Definición de la malla y dimensiones
    estado.Nx = round(cfg.a / cfg.dx);
    estado.Ny = round(cfg.b / cfg.dy);
    
    if strcmp(cfg.modelo, '3D_1Banda')
        estado.Nz = round(cfg.c / cfg.dz);
        % Coordenadas de la caja interna (muestra)
        estado.x1 = round((cfg.a - cfg.aa) / 2.0 / cfg.dx);
        estado.x2 = round((cfg.a + cfg.aa) / 2.0 / cfg.dx);
        estado.y1 = round((cfg.b - cfg.bb) / 2.0 / cfg.dy);
        estado.y2 = round((cfg.b + cfg.bb) / 2.0 / cfg.dy);
        estado.z1 = round((cfg.c - cfg.cc) / 2.0 / cfg.dz);
        estado.z2 = round((cfg.c + cfg.cc) / 2.0 / cfg.dz);
        
        estado.jxjyjz = (estado.x2 - estado.x1) * (estado.y2 - estado.y1) * (estado.z2 - estado.z1);
        
        % Cálculo de paso temporal estable (CFL)
        dl = 2 / (1/cfg.dx^2 + 1/cfg.dy^2 + 1/cfg.dz^2);  
        estado.dt = 0.99 * min([dl/4, dl * cfg.bt / (4 * cfg.kappa^2)]);
        
        % Coeficientes de evolución numérica 3D
        estado.rx = estado.dt / (cfg.dx^2);    
        estado.ry = estado.dt / (cfg.dy^2);
        estado.rz = estado.dt / (cfg.dz^2);
        estado.c1 = estado.dt * (1 - cfg.T); 
        estado.d1 = estado.dt * (1 - cfg.T);  
        
        estado.sxy = (estado.dt * cfg.kappa^2) * (cfg.dx / cfg.dy); 
        estado.sxz = (estado.dt * cfg.kappa^2) * (cfg.dx / cfg.dz);
        estado.syx = (estado.dt * cfg.kappa^2) * (cfg.dy / cfg.dx);
        estado.syz = (estado.dt * cfg.kappa^2) * (cfg.dy / cfg.dz);
        estado.szx = (estado.dt * cfg.kappa^2) * (cfg.dz / cfg.dx);
        estado.szy = (estado.dt * cfg.kappa^2) * (cfg.dz / cfg.dy);
        
        estado.currentx = (1 - cfg.T / cfg.dx);
        estado.currenty = (1 - cfg.T / cfg.dy);
        
        % 2. Inicialización de Matrices 3D (Vectorizada)
        % Pre-asignamos ceros a todo el dominio (vacío)
        estado.G = zeros(estado.Nx+1, estado.Ny+1, estado.Nz+1);
        
        % Nucleación del estado superconductor (G = 1) solo en la caja interna
        estado.G(estado.x1:estado.x2+1, estado.y1:estado.y2+1, estado.z1:estado.z2+1) = 1.0;
        
        estado.taux = zeros(estado.Nx+1, estado.Ny+1, estado.Nz+1);
        estado.tauy = zeros(estado.Nx+1, estado.Ny+1, estado.Nz+1);
        estado.tauz = zeros(estado.Nx+1, estado.Ny+1, estado.Nz+1);

        % 3. Aplicar Variante Geométrica de TAU (La que elija el usuario)
        switch cfg.geometria_tau
            case 'bloque'
                % El código activo original: bloque completo
                estado.taux(estado.x1:estado.x2+1, estado.y1:estado.y2+1, estado.z1:estado.z2+1) = 1.0;
                estado.tauy(estado.x1:estado.x2+1, estado.y1:estado.y2+1, estado.z1:estado.z2+1) = 1.0;
                estado.tauz(estado.x1:estado.x2+1, estado.y1:estado.y2+1, estado.z1:estado.z2+1) = 1.0;
                
            case 'estricto'
                % El código comentado original vectorizado (evita fugas en bordes)
                % Índices extraídos lógicamente de tus desigualdades originales
                estado.taux(estado.x1:estado.x2-1, estado.y1+1:estado.y2-1, estado.z1+1:estado.z2-1) = 1.0;
                estado.tauy(estado.x1+1:estado.x2-1, estado.y1:estado.y2-1, estado.z1+1:estado.z2-1) = 1.0;
                estado.tauz(estado.x1+1:estado.x2-1, estado.y1+1:estado.y2-1, estado.z1:estado.z2-1) = 1.0;
        end
        
        % Resto de variables 3D
        estado.F = ones(estado.Nx+1, estado.Ny+1, estado.Nz+1);
        estado.thetax = zeros(estado.Nx, estado.Ny+1, estado.Nz+1);  
        estado.thetay = zeros(estado.Nx+1, estado.Ny, estado.Nz+1);  
        estado.thetaz = zeros(estado.Nx+1, estado.Ny+1, estado.Nz);  
        
        estado.phix = zeros(estado.Nx, estado.Ny+1, estado.Nz+1);
        estado.phiy = zeros(estado.Nx+1, estado.Ny, estado.Nz+1);
        estado.phiz = zeros(estado.Nx+1, estado.Ny+1, estado.Nz);
        
        estado.Ux = exp(-1i * estado.thetax);        
        estado.Uy = exp(-1i * estado.thetay);
        estado.Uz = exp(-1i * estado.thetaz);
        
        estado.Vx = estado.Ux;        
        estado.Vy = estado.Uy;
        estado.Vz = estado.Uz;
        
        estado.Qx = zeros(estado.Nx, estado.Ny+1, estado.Nz+1);  
        estado.Qy = zeros(estado.Nx+1, estado.Ny, estado.Nz+1);  
        estado.Qz = zeros(estado.Nx+1, estado.Ny+1, estado.Nz);  
        
        estado.hx = zeros(estado.Nx+1, estado.Ny, estado.Nz);      
        estado.hy = zeros(estado.Nx, estado.Ny+1, estado.Nz);
        estado.hz = zeros(estado.Nx, estado.Ny, estado.Nz+1);
        
    elseif strcmp(cfg.modelo, '2D_2Bandas')
        estado.Nx = round(cfg.a / cfg.dx);
        estado.Ny = round(cfg.b / cfg.dy);
        estado.NxNy = estado.Nx * estado.Ny;
        
        % Límite temporal de estabilidad y coeficientes numéricos
        dl = 2 / (1/cfg.dx^2 + 1/cfg.dy^2);
        estado.dt = 0.99 * min([dl/4, dl * cfg.bt / (4 * cfg.kappa^2)]);
        
        estado.rx = estado.dt / cfg.dx^2;
        estado.ry = estado.dt / cfg.dy^2;
        estado.c = estado.dt * (1 - cfg.T);
        estado.txy = (cfg.kappa^2 * estado.dt * cfg.dx) / (cfg.bt * cfg.dy);
        estado.tyx = (cfg.kappa^2 * estado.dt * cfg.dy) / (cfg.bt * cfg.dx);
        estado.dxdy = cfg.dx * cfg.dy;
        
        % Condiciones iniciales del superconductor perfecto en 2 bandas
        estado.G  = ones(estado.Nx+1, estado.Ny+1);
        estado.G2 = ones(estado.Nx+1, estado.Ny+1);
        estado.F  = ones(estado.Nx+1, estado.Ny+1);
        estado.F3 = ones(estado.Nx+1, estado.Ny+1);
        estado.E  = ones(estado.Nx+1, estado.Ny+1);
        
        % Potencial vector y variables de enlace (Eje X)
        estado.thetax = zeros(estado.Nx, estado.Ny+1);
        estado.phix   = zeros(estado.Nx, estado.Ny+1);
        estado.Ux     = exp(-1i * estado.thetax);
        estado.Qx     = zeros(estado.Nx, estado.Ny+1);
        
        % Potencial vector y variables de enlace (Eje Y)
        estado.thetay = zeros(estado.Nx+1, estado.Ny);
        estado.phiy   = zeros(estado.Nx+1, estado.Ny);
        estado.Uy     = exp(-1i * estado.thetay);
        estado.Qy     = zeros(estado.Nx+1, estado.Ny);
        
        estado.Vx = estado.Ux;        
        estado.Vy = estado.Uy;
        
        % Fases iniciales (solo se calculan al inicio de cada escalón magnético)
        estado.phase  = imag(log(estado.F));
        estado.phase3 = imag(log(estado.F3));
        
        % Campo magnético local inicial B = rot(A)
        estado.hz = zeros(estado.Nx, estado.Ny);
        estado.hz(1:estado.Nx, 1:estado.Ny) = (estado.thetay(2:estado.Nx+1, 1:estado.Ny) ...
                                             - estado.thetay(1:estado.Nx, 1:estado.Ny) ...
                                             - estado.thetax(1:estado.Nx, 2:estado.Ny+1) ...
                                             + estado.thetax(1:estado.Nx, 1:estado.Ny)) / estado.dxdy;
    end
    
    estado.iteraciones = 0; % Contador de pasos temporales
end