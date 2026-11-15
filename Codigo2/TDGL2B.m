format long;
clear all;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CREACIÓN DE DIRECTORIOS DE SALIDA
% Aquí se guardarán los resultados del parámetro de orden (psi), 
% los campos magnéticos (field), eléctricos (efield) y la fase.
mkdir('restart/');
mkdir('output/psi/');
mkdir('output/field/');
mkdir('output/efieldx/');
mkdir('output/efieldy/');
mkdir('output/phase/');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% PARÁMETROS GEOMÉTRICOS Y DE MALLA
a = 10; % Tamaño de la caja en x
b = 10; % Tamaño de la caja en y
dx = 0.25; % Paso espacial en x
dy = 0.25; % Paso espacial en y
dpi = 2.0.*pi;
dxdydpi=dx.*dy.*dpi;
k = 1;  % Parámetro de Ginzburg-Landau (kappa)
bt = 1; % Coeficiente de relajación
p = 1;  % Índice del bucle de campo magnético
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% PARÁMETROS TERMODINÁMICOS Y CAMPO EXTERNO
T=0.0; % Temperatura reducida (T/Tc)
Hi = 0.0; % Campo magnético inicial
Hf = 2;   % Campo magnético final
dH = 0.1; % Paso del campo magnético
H = (Hi:dH:Hf); % Vector de campos aplicados
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% PARÁMETROS NUMÉRICOS
eps = 0.00001; % Tolerancia para la convergencia del estado estacionario
is = 0;        % Bandera para iniciar desde cero (0) o cargar datos (1)
iMag = 1;
Mag(1,1) = 0;
Mag(1,2) = 0;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Nx = a/dx; % Número de puntos en x
Ny = b/dy; % Número de puntos en y
NxNy=Nx.*Ny;
% ESTABILIDAD TEMPORAL (Condición CFL)
dl = 2/(1/dx^2+1/dy^2);
dt = min([dl/4 dl*bt/(4*k^2)]);
dt = 0.99*dt; % Paso temporal ajustado para estabilidad
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% COEFICIENTES PARA EL ESQUEMA DE DIFERENCIAS FINITAS
rx = dt/dx^2;
ry = dt/dy^2;
c = dt*(1-T);
sx = (1-T)*dt/bt;
sy = (1-T)*dt/bt;
txy = (k^2*dt*dx)/(bt*dy);
tyx = (k^2*dt*dy)/(bt*dx);
dxdy = dx*dy;
% Coeficientes de normalización de energías
CMxy = 0.5*(1-T)*dx/(k^2*dy)/(Nx*Ny);
CMyx = 0.5*(1-T)*dy/(k^2*dx)/(Nx*Ny);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CONSTANTES PARA EL CÁLCULO DE ENERGÍAS
CenergyC=(1-T)/Nx.*Ny;        % Energía cinética
CenergyCd=(1-T).^2/Nx.*Ny;    % Energía de condensación
CenergyF = k.^2/Nx.*Ny;       % Energía del campo magnético
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CREACIÓN DE LA MALLA ESPACIAL
x = (0:dx:a);
y = (0:dy:b);
[X,Y] = meshgrid(x,y);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if is == 0
    % CONDICIONES INICIALES (Sistema superconductor perfecto)
    G = ones(Nx+1,Ny+1);   % Parámetro de orden banda 1 (\psi_1)
    G2 = ones(Nx+1,Ny+1);  % Parámetro de orden banda 2 (\psi_2)
    F = ones(Nx+1,Ny+1);   % Actualización temporal de banda 1
    F3 = ones(Nx+1,Ny+1);  % Actualización temporal de banda 2
    E = ones(Nx+1,Ny+1);
    Gap=-0.001;  % Acoplamiento interbanda (efecto Josephson interno)
    
    % VARIABLES DE GAUGE Y POTENCIAL VECTOR
    thetax = zeros(Nx,Ny+1); % Componente x del potencial vector (A_x)
    phix = zeros(Nx,Ny+1);
    Ux = exp(-1i*thetax);    % Variable de enlace U_x = exp(-i A_x dx)
    Qx = zeros(Nx,Ny+1);     % Supercorriente en x
    
    thetay = zeros(Nx+1,Ny); % Componente y del potencial vector (A_y)
    phiy = zeros(Nx+1,Ny);
    Uy = exp(-1i*thetay);    % Variable de enlace U_y = exp(-i A_y dy)
    Qy = zeros(Nx+1,Ny);     % Supercorriente en y
    
    Vx = exp(-1i*thetax);    % Variables de enlace temporales
    Vy = exp(-1i*thetay);
    
    phase = imag(log(F));    % Fase del parámetro de orden de la banda 1
    phase3 = imag(log(F3));  % Fase del parámetro de orden de la banda 2
    
    % Campo magnético local B_z = rot(A)_z
    hz(1:Nx,1:Ny) = (thetay(2:Nx+1,1:Ny)-thetay(1:Nx,1:Ny)-thetax(1:Nx,2:Ny+1)+thetax(1:Nx,1:Ny))/dxdy;
else
    % CARGAR ESTADO ANTERIOR SI is != 0
    load restart/G.mat;
    load restart/Ux.mat;
    load restart/Uy.mat;
    load restart/thetax.mat;
    load restart/thetay.mat;
    load restart/hz.mat;
    load restart/p.mat;
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Cooper0 = abs(G);
fieldOld   = hz;
nMax = 10000000; % Iteraciones máximas
lMax = 100;
mMax = nMax/lMax;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% BUCLE PRINCIPAL SOBRE EL CAMPO MAGNÉTICO EXTERNO
while H(p) <= Hf 
    save('restart/G.mat','G');
    save('restart/Ux.mat','Ux');
    save('restart/Uy.mat','Uy');
    save('restart/thetax.mat','thetax');
    save('restart/thetay.mat','thetay');
    save('restart/hz.mat','hz');
    save('restart/p.mat','p');
    m = 1;
    % BUCLE DE RELAJACIÓN TEMPORAL (Evolución hacia el estado estacionario)
    while m <= mMax     
        l = 1;        
          while l <= lMax
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%           
% ECUACIONES DEPENDIENTES DEL TIEMPO DE GINZBURG-LANDAU (TDGL)
% Discretización espacial usando variables de enlace U (invariantes de gauge) para derivadas covariantes.
% Actualización param de orden Banda 1 (G): incluye término de acoplamiento de fase con Banda 2 (Gap).
F(2:Nx,2:Ny) = G(2:Nx,2:Ny)+rx*(Vx(2:Nx,2:Ny).*G(3:Nx+1,2:Ny)-2*G(2:Nx,2:Ny)+conj(Vx(1:Nx-1,2:Ny)).*G(1:Nx-1,2:Ny))...
+ry*(Vy(2:Nx,2:Ny).*G(2:Nx,3:Ny+1)-2*G(2:Nx,2:Ny)+conj(Vy(2:Nx,1:Ny-1)).*G(2:Nx,1:Ny-1))...
+(dt*(1-T)).*G(2:Nx,2:Ny).*(1-abs(G(2:Nx,2:Ny)).^2)+Gap.*(abs(G2(2:Nx,2:Ny))).*(sin(phase3(2:Nx,2:Ny)));

% Actualización param de orden Banda 2 (G2): equivalente a banda 1.
F3(2:Nx,2:Ny) = G2(2:Nx,2:Ny)+rx*(Vx(2:Nx,2:Ny).*G2(3:Nx+1,2:Ny)-2*G2(2:Nx,2:Ny)+conj(Vx(1:Nx-1,2:Ny)).*G2(1:Nx-1,2:Ny))...
+ry*(Vy(2:Nx,2:Ny).*G2(2:Nx,3:Ny+1)-2*G2(2:Nx,2:Ny)+conj(Vy(2:Nx,1:Ny-1)).*G2(2:Nx,1:Ny-1))...
+(dt*(1-T)).*G2(2:Nx,2:Ny).*(1-abs(G2(2:Nx,2:Ny)).^2)-Gap.*(abs(G(2:Nx,2:Ny))).*(sin(phase(2:Nx,2:Ny)));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CÁLCULO DE LA SUPERCORRIENTE EN X Y ACTUALIZACIÓN DEL POTENCIAL VECTOR A_x
Qx(1:Nx,2:Ny) = imag(conj(G(1:Nx,2:Ny)).*Vx(1:Nx,2:Ny).*G(2:Nx+1,2:Ny))+Gap.*imag(conj(G2(1:Nx,2:Ny)).*Vx(1:Nx,2:Ny).*G2(2:Nx+1,2:Ny));
phix(1:Nx,2:Ny) = thetax(1:Nx,2:Ny)+((1-T).*dt).*Qx(1:Nx,2:Ny)-txy*(hz(1:Nx,2:Ny)-hz(1:Nx,1:Ny-1));
Ux = exp(-1i*phix); % Nueva variable de enlace U_x
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CÁLCULO DE LA SUPERCORRIENTE EN Y Y ACTUALIZACIÓN DEL POTENCIAL VECTOR A_y
Qy(2:Nx,1:Ny) = imag(conj(G(2:Nx,1:Ny)).*Vy(2:Nx,1:Ny).*G(2:Nx,2:Ny+1))+Gap.*imag(conj(G2(2:Nx,1:Ny)).*Vy(2:Nx,1:Ny).*G2(2:Nx,2:Ny+1));
phiy(2:Nx,1:Ny) = thetay(2:Nx,1:Ny)+((1-T).*dt).*Qy(2:Nx,1:Ny)+tyx*(hz(2:Nx,1:Ny)-hz(1:Nx-1,1:Ny));
Uy = exp(-1i*phiy); % Nueva variable de enlace U_y
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ACTUALIZACIÓN DEL CAMPO MAGNÉTICO LOCAL (Ecuaciones de Maxwell rot(A) = B)
hz(2:Nx-1,2:Ny-1) = (phiy(3:Nx,2:Ny-1)-phiy(2:Nx-1,2:Ny-1)-phix(2:Nx-1,3:Ny)+phix(2:Nx-1,2:Ny-1))/dxdy;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CONDICIONES DE FRONTERA PARA EL PARÁMETRO DE ORDEN (Aislante / Neumann) Banda 1
F(1,2:Ny) = Ux(1,2:Ny).*F(2,2:Ny);
F(Nx+1,2:Ny) = conj(Ux(Nx,2:Ny)).*F(Nx,2:Ny);
F(2:Nx,1) = Uy(2:Nx,1).*F(2:Nx,2);
F(2:Nx,Ny+1) = conj(Uy(2:Nx,Ny)).*F(2:Nx,Ny);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CONDICIONES DE FRONTERA PARA EL PARÁMETRO DE ORDEN Banda 2
F3(1,2:Ny) = Ux(1,2:Ny).*F3(2,2:Ny);
F3(Nx+1,2:Ny) = conj(Ux(Nx,2:Ny)).*F3(Nx,2:Ny);
F3(2:Nx,1) = Uy(2:Nx,1).*F3(2:Nx,2);
F3(2:Nx,Ny+1) = conj(Uy(2:Nx,Ny)).*F3(2:Nx,Ny);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CONDICIÓN DE FRONTERA DEL CAMPO MAGNÉTICO (Igual al campo externo H aplicado en los bordes)
hz(1,1:Ny)  = H(p);
hz(Nx,1:Ny) = H(p);
hz(2:Nx-1,1)  = H(p);
hz(2:Nx-1,Ny) = H(p);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Electric potential and electric field%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%            
            % PREPARAR VARIABLES PARA LA SIGUIENTE ITERACIÓN
            G = F;
            G2 = F3;
            thetax = phix;
            thetay = phiy;
            Vx = Ux;
            Vy = Uy;

            l = l+1;
        end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUAVIZADO EN LAS ESQUINAS PARA LA BANDA 1
F(1,1) = 0.5*(F(2,1)+F(1,2));
F(1,Ny+1) = 0.5*(F(1,Ny)+F(2,Ny+1));
F(Nx+1,1) = 0.5*(F(Nx,1)+F(Nx+1,2));
F(Nx+1,Ny+1) = 0.5*(F(Nx,Ny+1)+F(Nx+1,Ny));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUAVIZADO EN LAS ESQUINAS PARA LA BANDA 2
F3(1,1) = 0.5*(F3(2,1)+F3(1,2));
F3(1,Ny+1) = 0.5*(F3(1,Ny)+F3(2,Ny+1));
F3(Nx+1,1) = 0.5*(F3(Nx,1)+F3(Nx+1,2));
F3(Nx+1,Ny+1) = 0.5*(F3(Nx,Ny+1)+F3(Nx+1,Ny));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%     
% CRITERIO DE CONVERGENCIA
% Verifica si la diferencia entre iteraciones del parámetro de orden es menor a la tolerancia 'eps'
Cooper1= abs(F);
diff = 0.0;
for j = 1:Ny+1
  for i = 1:Nx+1
  dif = abs(Cooper1(i,j)-Cooper0(i,j));
  Cooper0(i,j) = Cooper1(i,j);
    if (dif>diff) 
      diff = dif;
            end 
        end 
    end 
  
  diffh = 0.0;
  % Verifica la convergencia del campo magnético local
  for  j = 1:Ny
      for  i = 1:Nx
                        difh = abs(hz(i,j)-fieldOld(i,j));
                        fieldOld(i,j) = hz(i,j);
                        if (difh>diffh) 
                            diffh = difh;
                end 
      end 
 end 

        
        % Romper el bucle si ambos, parámetro de orden y campo, han convergido
        if ((diff<eps)&&(diffh<eps))
            break;
        else
            E = F;
        end

        m = m+1;
    end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% EXTRACCIÓN DE OBSERVABLES FÍSICOS AL ALCANZAR EL ESTADO ESTACIONARIO
d = abs(F);    % Módulo del parámetro de orden banda 1 (densidad de pares de Cooper)
d5=F;
d3 = abs(F).*abs(F);
d2 = abs(log(F));
B=abs(F3);     % Módulo del parámetro de orden banda 2
phase = imag(log(F));   % Fase superconductora banda 1
phase3 = imag(log(F3)); % Fase superconductora banda 2
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CÁLCULO DE LA MAGNETIZACIÓN GLOBAL
fluxNew = 0.0;
for j = 1:Ny
    for i = 1:Nx
        fluxNew = hz(i,j)+fluxNew; % Flujo magnético total
    end 
end 
  
    Bz      = fluxNew/NxNy; % Inducción magnética promedio
    aMgzt   = H(p)-Bz;      % Magnetización (M = H - B)
    
        
    Magt2(p,1) = H(p);
    Magt2(p,2) = aMgzt;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CÁLCULO DE LA ENERGÍA LIBRE DE GINZBURG-LANDAU
% 1. Energía Cinética (Términos de gradiente invariantes de gauge)
energyC = 0.0;
for j = 2:Ny
 for  i = 2:Nx
aa      = abs(Ux(i,j)*d5(i+1,j)-d5(i,j))/Nx;
energyC = energyC+aa*aa;
aa      = abs(Uy(i,j)*d5(i,j+1)-d5(i,j))/Ny;
energyC = energyC+aa.*aa;
 end
end

% 2. Energía de Condensación (Términos de potencial \alpha|\psi|^2 + \beta|\psi|^4)
energyCd=0.0;
for j = 2:Ny
  for i = 2:Nx
energyCd = energyCd+d3(i,j)*(0.5.*d3(i,j)-1.0);
   end
end
energyCd = ((1-T).^2/Nx.*Ny).*energyCd;

% 3. Energía del Campo Magnético ( (h - H)^2 )
energyF = 0.0;
  for  j = 1:Ny
    for  i = 1:Nx
      aa      = hz(i,j)-H(p);
       energyF = energyF+aa*aa;
    end
   end
energyF = CenergyF*energyF;

energy = energyC+energyCd+energyF; % Energía total del sistema

energy2(p,1)=H(p);
energy2(p,2) = energyC;

energy3(p,1)=H(p);
energy3(p,2) = energyCd;

energy4(p,1)=H(p);
energy4(p,2) = energy; 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % GRÁFICAS EN TIEMPO REAL
    subplot(2,2,1);
    plot(Magt2(:,1),Magt2(:,2),'LineWidth',2); % Curva de Magnetización

    subplot(2,2,2);
    plot(energy4(:,1),energy4(:,2),'LineWidth',2); % Perfil de Energía

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % EXPORTACIÓN DE DATOS (OUTPUTS)
    % Crea subdirectorios para cada valor de campo aplicado y guarda las matrices.
    dir = num2str(H(p));

    mkdir('output/psi',dir);
    mkdir('output/field/',dir);
    mkdir('output/phase/',dir);
    mkdir('output/efieldx/',dir);
    mkdir('output/efieldy/',dir);

    file = strcat('output/psi/',dir,'/d.mat');
    save(file,'d');
    
    file = strcat('output/psi/',dir,'/B.mat');
    save(file,'B');
    
    file = strcat('output/psi/',dir,'/d2.mat');
    save(file,'d2');

    file = strcat('output/field/',dir,'/hz.mat');
    save(file,'hz');
   
    file = strcat('output/phase/',dir,'/phase.mat');
    save(file,'phase');

    p = p+1; % Incrementar al siguiente campo magnético
end