format long;
clear all;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
mkdir('restart/');
mkdir('output/psi/');
mkdir('output/field/');
mkdir('output/efieldx/');
mkdir('output/efieldy/');
mkdir('output/phase/');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
a = 10;
b = 10;
dx = 0.25;
dy = 0.25;
dpi = 2.0.*pi;
dxdydpi=dx.*dy.*dpi;
k = 1;
bt = 1;
p = 1;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
T=0.0;
Hi = 0.0;
Hf = 2;
dH = 0.1;
H = (Hi:dH:Hf);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
eps = 0.00001;
is = 0;
iMag = 1;
Mag(1,1) = 0;
Mag(1,2) = 0;
#Probe
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Nx = a/dx;
Ny = b/dy;
NxNy=Nx.*Ny;
dl = 2/(1/dx^2+1/dy^2);
dt = min([dl/4 dl*bt/(4*k^2)]);
dt = 0.99*dt;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
rx = dt/dx^2;
ry = dt/dy^2;
c = dt*(1-T);
sx = (1-T)*dt/bt;
sy = (1-T)*dt/bt;
txy = (k^2*dt*dx)/(bt*dy);
tyx = (k^2*dt*dy)/(bt*dx);
dxdy = dx*dy;
CMxy = 0.5*(1-T)*dx/(k^2*dy)/(Nx*Ny);
CMyx = 0.5*(1-T)*dy/(k^2*dx)/(Nx*Ny);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
CenergyC=(1-T)/Nx.*Ny;
CenergyCd=(1-T).^2/Nx.*Ny;
CenergyF = k.^2/Nx.*Ny;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
x = (0:dx:a);
y = (0:dy:b);
[X,Y] = meshgrid(x,y);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if is == 0
    G = ones(Nx+1,Ny+1);  % band 1
    G2 = ones(Nx+1,Ny+1);  % band2
    F = ones(Nx+1,Ny+1);
    F3 = ones(Nx+1,Ny+1);
    E = ones(Nx+1,Ny+1);
    Gap=-0.001;  % healing Coupling
    thetax = zeros(Nx,Ny+1);
    phix = zeros(Nx,Ny+1);
    Ux = exp(-1i*thetax);
    Qx = zeros(Nx,Ny+1);
    thetay = zeros(Nx+1,Ny);
    phiy = zeros(Nx+1,Ny);
    Uy = exp(-1i*thetay);
    Qy = zeros(Nx+1,Ny);
    Vx = exp(-1i*thetax);        % transfer the link variables
    Vy = exp(-1i*thetay);
    phase = imag(log(F));
    phase3 = imag(log(F3));
    hz(1:Nx,1:Ny) = (thetay(2:Nx+1,1:Ny)-thetay(1:Nx,1:Ny)-thetax(1:Nx,2:Ny+1)+thetax(1:Nx,1:Ny))/dxdy;
else
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
nMax = 10000000;
lMax = 100;
mMax = nMax/lMax;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
while H(p) <= Hf 
    save('restart/G.mat','G');
    save('restart/Ux.mat','Ux');
    save('restart/Uy.mat','Uy');
    save('restart/thetax.mat','thetax');
    save('restart/thetay.mat','thetay');
    save('restart/hz.mat','hz');
    save('restart/p.mat','p');
    m = 1;
    while m <= mMax     
        l = 1;        
          while l <= lMax
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%           
F(2:Nx,2:Ny) = G(2:Nx,2:Ny)+rx*(Vx(2:Nx,2:Ny).*G(3:Nx+1,2:Ny)-2*G(2:Nx,2:Ny)+conj(Vx(1:Nx-1,2:Ny)).*G(1:Nx-1,2:Ny))...
+ry*(Vy(2:Nx,2:Ny).*G(2:Nx,3:Ny+1)-2*G(2:Nx,2:Ny)+conj(Vy(2:Nx,1:Ny-1)).*G(2:Nx,1:Ny-1))...
+(dt*(1-T)).*G(2:Nx,2:Ny).*(1-abs(G(2:Nx,2:Ny)).^2)+Gap.*(abs(G2(2:Nx,2:Ny))).*(sin(phase3(2:Nx,2:Ny)));

F3(2:Nx,2:Ny) = G2(2:Nx,2:Ny)+rx*(Vx(2:Nx,2:Ny).*G2(3:Nx+1,2:Ny)-2*G2(2:Nx,2:Ny)+conj(Vx(1:Nx-1,2:Ny)).*G2(1:Nx-1,2:Ny))...
+ry*(Vy(2:Nx,2:Ny).*G2(2:Nx,3:Ny+1)-2*G2(2:Nx,2:Ny)+conj(Vy(2:Nx,1:Ny-1)).*G2(2:Nx,1:Ny-1))...
+(dt*(1-T)).*G2(2:Nx,2:Ny).*(1-abs(G2(2:Nx,2:Ny)).^2)-Gap.*(abs(G(2:Nx,2:Ny))).*(sin(phase(2:Nx,2:Ny)));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Qx(1:Nx,2:Ny) = imag(conj(G(1:Nx,2:Ny)).*Vx(1:Nx,2:Ny).*G(2:Nx+1,2:Ny))+Gap.*imag(conj(G2(1:Nx,2:Ny)).*Vx(1:Nx,2:Ny).*G2(2:Nx+1,2:Ny));
phix(1:Nx,2:Ny) = thetax(1:Nx,2:Ny)+((1-T).*dt).*Qx(1:Nx,2:Ny)-txy*(hz(1:Nx,2:Ny)-hz(1:Nx,1:Ny-1));
Ux = exp(-1i*phix);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Qy(2:Nx,1:Ny) = imag(conj(G(2:Nx,1:Ny)).*Vy(2:Nx,1:Ny).*G(2:Nx,2:Ny+1))+Gap.*imag(conj(G2(2:Nx,1:Ny)).*Vy(2:Nx,1:Ny).*G2(2:Nx,2:Ny+1));
phiy(2:Nx,1:Ny) = thetay(2:Nx,1:Ny)+((1-T).*dt).*Qy(2:Nx,1:Ny)+tyx*(hz(2:Nx,1:Ny)-hz(1:Nx-1,1:Ny));
Uy = exp(-1i*phiy);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
hz(2:Nx-1,2:Ny-1) = (phiy(3:Nx,2:Ny-1)-phiy(2:Nx-1,2:Ny-1)-phix(2:Nx-1,3:Ny)+phix(2:Nx-1,2:Ny-1))/dxdy;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
F(1,2:Ny) = Ux(1,2:Ny).*F(2,2:Ny);
F(Nx+1,2:Ny) = conj(Ux(Nx,2:Ny)).*F(Nx,2:Ny);
F(2:Nx,1) = Uy(2:Nx,1).*F(2:Nx,2);
F(2:Nx,Ny+1) = conj(Uy(2:Nx,Ny)).*F(2:Nx,Ny);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
F3(1,2:Ny) = Ux(1,2:Ny).*F3(2,2:Ny);
F3(Nx+1,2:Ny) = conj(Ux(Nx,2:Ny)).*F3(Nx,2:Ny);
F3(2:Nx,1) = Uy(2:Nx,1).*F3(2:Nx,2);
F3(2:Nx,Ny+1) = conj(Uy(2:Nx,Ny)).*F3(2:Nx,Ny);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
hz(1,1:Ny)  = H(p);
hz(Nx,1:Ny) = H(p);
hz(2:Nx-1,1)  = H(p);
hz(2:Nx-1,Ny) = H(p);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Electric potential and electric field%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%            
            G = F;
            
            G2 = F3;

            thetax = phix;

            thetay = phiy;
            
            Vx = Ux;
            
            Vy = Uy;


            l = l+1;

          
        end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
F(1,1) = 0.5*(F(2,1)+F(1,2));
F(1,Ny+1) = 0.5*(F(1,Ny)+F(2,Ny+1));
F(Nx+1,1) = 0.5*(F(Nx,1)+F(Nx+1,2));
F(Nx+1,Ny+1) = 0.5*(F(Nx,Ny+1)+F(Nx+1,Ny));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
F3(1,1) = 0.5*(F3(2,1)+F3(1,2));
F3(1,Ny+1) = 0.5*(F3(1,Ny)+F3(2,Ny+1));
F3(Nx+1,1) = 0.5*(F3(Nx,1)+F3(Nx+1,2));
F3(Nx+1,Ny+1) = 0.5*(F3(Nx,Ny+1)+F3(Nx+1,Ny));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%     
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
  
  for  j = 1:Ny
	  for  i = 1:Nx
						difh = abs(hz(i,j)-fieldOld(i,j));
						fieldOld(i,j) = hz(i,j);
						if (difh>diffh) 
			    			diffh = difh;
				end 
      end 
 end 

        
        
        if ((diff<eps)&&(diffh<eps))

            break;

        else

            E = F;

        end

        m = m+1;

        

    end

 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
d = abs(F);
d5=F;
d3 = abs(F).*abs(F);
d2 = abs(log(F));
B=abs(F3);
phase = imag(log(F));
phase3 = imag(log(F3));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fluxNew = 0.0;
for j = 1:Ny
	for i = 1:Nx
		fluxNew = hz(i,j)+fluxNew;
	end 
end 
  
    Bz      = fluxNew/NxNy;
	aMgzt   = H(p)-Bz;
    
        
    Magt2(p,1) = H(p);
    Magt2(p,2) = aMgzt;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
energyC = 0.0;
 
for j = 2:Ny
 for  i = 2:Nx
aa      = abs(Ux(i,j)*d5(i+1,j)-d5(i,j))/Nx;
energyC = energyC+aa*aa;
aa      = abs(Uy(i,j)*d5(i,j+1)-d5(i,j))/Ny;
energyC = energyC+aa.*aa;
 end
end



energyCd=0.0;
for j = 2:Ny
  for i = 2:Nx
energyCd = energyCd+d3(i,j)*(0.5.*d3(i,j)-1.0);
   end
end
energyCd = ((1-T).^2/Nx.*Ny).*energyCd;

energyF = 0.0;
  for  j = 1:Ny
    for  i = 1:Nx
      aa      = hz(i,j)-H(p);
       energyF = energyF+aa*aa;
    end
   end
energyF = CenergyF*energyF;

energy = energyC+energyCd+energyF;

energy2(p,1)=H(p);
energy2(p,2) = energyC;% 

energy3(p,1)=H(p);
energy3(p,2) = energyCd;% 

energy4(p,1)=H(p);
energy4(p,2) = energy;% 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    subplot(2,2,1);
    plot(Magt2(:,1),Magt2(:,2),'LineWidth',2);

    subplot(2,2,2);
    plot(energy4(:,1),energy4(:,2),'LineWidth',2);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
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

    p = p+1;

    

end

