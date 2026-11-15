format long;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
mkdir('restart/');
mkdir('output/psi/');
mkdir('output/field/');
mkdir('output/phase/');
mkdir('output/currentsx/');
mkdir('output/currentsy/');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
dx = 0.25;
dy = 0.25;
dz = 0.25;
a = 20;%external box{x}
b = 20;%external box{y}
c = 10;%external box{z}

aa = 10;%internal box{x}
bb = 10;%internal box{y}
cc = 5;%internal box{z}

Nx = round(a/dx); %size of the all system.
Ny = round(b/dy);
Nz = round(c/dz);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
x1 = round((a-aa)/2.0/dx); % coordinates of the internal box
x2 = round((a+aa)/2.0/dx);
y1 = round((b-bb)/2.0/dy);
y2 = round((b+bb)/2.0/dy);
z1 = round((c-cc)/2.0/dz);
z2 = round((c+cc)/2.0/dz);
jxjyjz  = (x2-x1).*(y2-y1).*(z2-z1) ;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
k = 1;
bt = 1;
Hi = 0.0;Hf = 2;dH = 0.1;
H = (Hi:dH:Hf);
T=0.0;
p = 1;
eps = 0.0000001; %tolerance
is = 0;      %%% Start
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
dxdy= dx.*dy;    
dydz= dy.*dz;
dzdx= dz.*dx;
dl = 2/(1/dx.^2+1/dy.^2+1/dz.^2);  %time for time convergence.
dt = min([dl/4 dl.*bt/(4.*k.^2)]);
dt = 0.99.*dt;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
c1 = dt.*(1-T); 
d1 = dt.*(1-T);  
CenergyF = k.^2/jxjyjz;
rx  = dt/(dx.^2);    
ry  = dt/(dy.^2);
rz  = dt/(dz.^2);
sxy = (dt*k.^2).*(dx/dy); %% Layer 1 and 3
sxz = (dt*k.^2).*(dx/dz);
syx = (dt*k.^2).*(dy/dx);
syz = (dt*k^.2).*(dy/dz);
szx = (dt*k^2).*(dz/dx);
szy = (dt*k^2).*(dz/dy);
CenergyC=(1-T)/jxjyjz;
CenergyCd=(1-T).^2/jxjyjz;
CenergyF = k.^2/jxjyjz;
currentx=(1-T/dx);
currenty=(1-T/dy);
x = (0:dx:a); %% mesh for  slice figure
y = (0:dy:b);
z = (0:dy:c);
[X,Y] = meshgrid(x,y); %Grid
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      

if is == 0   %%% initial conditions
 
for n=1:Nz+1
 for m=1:Ny+1
  for i=1:Nx+1
       G(i,m,n)=0.0;
     
      end
    end
 end

 
for n=z1:z2+1
 for m=y1:y2+1
  for i=x1:x2+1
       G(i,m,n)=1.0;
      end
    end
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
for n=1:Nz+1
 for m=1:Ny+1
  for i=1:Nx+1
       taux(i,m,n)=0.0;
       tauy(i,m,n)=0.0;
       tauz(i,m,n)=0.0;
      end
    end
 end

 
for n=z1:z2+1
 for m=y1:y2+1
  for i=x1:x2+1
       taux(i,m,n)=1.0;
       tauy(i,m,n)=1.0;
       tauz(i,m,n)=1.0;
      end
    end
end


%for n=1:Nz+1
 % for m=1:Ny+1
  %  for i=1:Nx
   %  if ((i<x1)||(i>=x2)||(m<=y1)||(m>=y2)||(n<=z1)||(n>=z2))
    %  taux(i,m,n)=0.0;
     % else  
     % taux(i,m,n)=1.0;
     % end
    %end
  %end
%end


 

%for n=1:Nz+1
 % for m=1:Ny
  %  for i=1:Nx+1
   %   if ((i<=x1)||(i>=x2)||(m<y1)||(m>=y2)||(n<=z1)||(n>=z2))
    %     tauy(i,m,n)=0.0;
     % else  
     % tauy(i,m,n)=1.0;
     % end
    %end
  %end
%end  



%for n=1:Nz
 % for m=1:Ny+1
  %  for i=1:Nx+1
   %  if ((i<=x1)||(i>=x2)||(m<=y1)||(m>=y2)||(n<z1)||(n>=z2))
    %     tauz(i,m,n)=0.0;
     % else  
      %tauz(i,m,n)=1.0;
      %end
    %end
  %end
%end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
F=ones(Nx+1,Ny+1,Nz+1);
E =ones(Nx+1,Ny+1,Nz+1);    %orden parameter
thetax = zeros(Nx,Ny+1,Nz+1);  %$vec{A}_{x}$
thetay = zeros(Nx+1,Ny,Nz+1);  %$vec{A}_{y}$
thetaz = zeros(Nx+1,Ny+1,Nz);  %$vec{A}_{z}$
phix = zeros(Nx,Ny+1,Nz+1);
phiy = zeros(Nx+1,Ny,Nz+1);
phiz = zeros(Nx+1,Ny+1,Nz);
Ux = exp(-1i*thetax);        % link variables
Uy = exp(-1i*thetay);
Uz = exp(-1i*thetaz);
Vx = exp(-1i*thetax);        % transfer the link variables
Vy = exp(-1i*thetay);
Vz = exp(-1i*thetaz);
Qx = zeros(Nx,Ny+1,Nz+1);  % supercurrent{x}
Qy = zeros(Nx+1,Ny,Nz+1);  % supercurrent{y}
Qz = zeros(Nx+1,Ny+1,Nz);  % supercurrent{z}

hx=zeros(Nx+1,Ny,Nz);      % magnetic fields
hy=zeros(Nx,Ny+1,Nz);
hz=zeros(Nx,Ny,Nz+1);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      

else
    load restart/G.mat;
    load restart/Ux.mat;  
    load restart/Uy.mat;
    load restart/Uz.mat;
    load restart/Vx.mat;
    load restart/Vy.mat;  
    load restart/Vz.mat;
    load restart/thetax.mat;
    load restart/thetay.mat;
    load restart/thetaz.mat;  
    load restart/hz.mat;
    load restart/p.mat;
end

Cooper0 = abs(G);
fieldOld   = hz;
nMax = 10000000;
lMax = 100;
mMax = nMax/lMax;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
while H(p) <= Hf
    save('restart/G.mat','G');
    save('restart/Ux.mat','Ux');
    save('restart/Uy.mat','Uy');
    save('restart/Uz.mat','Uz');
    save('restart/thetax.mat','thetax');
    save('restart/thetay.mat','thetay');
    save('restart/thetaz.mat','thetaz');
    save('restart/hz.mat','hz');
    save('restart/p.mat','p');
    m = 1;  
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
    while m <= mMax
        l = 1;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
        while l <= lMax
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
F(x1+1:x2,y1+1:y2,z1+1:z2) = G(x1+1:x2,y1+1:y2,z1+1:z2)+rx.*(Vx(x1+1:x2,y1+1:y2,z1+1:z2).*G(x1+2:x2+1,y1+1:y2,z1+1:z2)-2.0.*G(x1+1:x2,y1+1:y2,z1+1:z2)+conj(Vx(x1:x2-1,y1+1:y2,z1+1:z2)).*G(x1:x2-1,y1+1:y2,z1+1:z2))...
+ry.*(Vy(x1+1:x2,y1+1:y2,z1+1:z2).*G(x1+1:x2,y1+2:y2+1,z1+1:z2)-2.0.*G(x1+1:x2,y1+1:y2,z1+1:z2)+conj(Vy(x1+1:x2,y1:y2-1,z1+1:z2)).*G(x1+1:x2,y1:y2-1,z1+1:z2))...
+rz.*(Vz(x1+1:x2,y1+1:y2,z1+1:z2).*G(x1+1:x2,y1+1:y2,z1+2:z2+1)-2.0.*G(x1+1:x2,y1+1:y2,z1+1:z2)+conj(Vz(x1+1:x2,y1+1:y2,z1:z2-1)).*G(x1+1:x2,y1+1:y2,z1:z2-1))...
+c1.*G(x1+1:x2,y1+1:y2,z1+1:z2).*(1.0-abs(G(x1+1:x2,y1+1:y2,z1+1:z2)).^2);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
Qx(1:Nx,2:Ny,2:Nz) = imag(conj(G(1:Nx,2:Ny,2:Nz)).*Vx(1:Nx,2:Ny,2:Nz).*G(2:Nx+1,2:Ny,2:Nz));
 
 phix(1:Nx,2:Ny,2:Nz) = thetax(1:Nx,2:Ny,2:Nz)+d1.*taux(1:Nx,2:Ny,2:Nz).*Qx(1:Nx,2:Ny,2:Nz)...
        -sxy.*(hz(1:Nx,2:Ny,2:Nz)-hz(1:Nx,1:Ny-1,2:Nz))+sxz*(hy(1:Nx,2:Ny,2:Nz)-hy(1:Nx,2:Ny,1:Nz-1));      
       
  Ux(1:Nx,2:Ny,2:Nz) = exp(-1i.*phix(1:Nx,2:Ny,2:Nz));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
    Qy(2:Nx,1:Ny,2:Nz) = imag(conj(G(2:Nx,1:Ny,2:Nz)).*Vy(2:Nx,1:Ny,2:Nz).*G(2:Nx,2:Ny+1,2:Nz));
 
    phiy(2:Nx,1:Ny,2:Nz) = thetay(2:Nx,1:Ny,2:Nz)+d1.*tauy(2:Nx,1:Ny,2:Nz).*Qy(2:Nx,1:Ny,2:Nz)...  
     -syz.*(hx(2:Nx,1:Ny,2:Nz)-hx(2:Nx,1:Ny,1:Nz-1))+syx.*(hz(2:Nx,1:Ny,2:Nz)-hz(1:Nx-1,1:Ny,2:Nz));
 
   
     Uy(2:Nx,1:Ny,2:Nz) = exp(-1i.*phiy(2:Nx,1:Ny,2:Nz));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
   
    Qz(2:Nx,2:Ny,1:Nz) = imag(conj(G(2:Nx,2:Ny,1:Nz)).*Vz(2:Nx,2:Ny,1:Nz).*G(2:Nx,2:Ny,2:Nz+1));

  phiz(2:Nx,2:Ny,1:Nz) = thetaz(2:Nx,2:Ny,1:Nz)+d1.*tauz(2:Nx,2:Ny,1:Nz).*Qz(2:Nx,2:Ny,1:Nz)...
          -szx.*(hy(2:Nx,2:Ny,1:Nz)-hy(1:Nx-1,2:Ny,1:Nz))+szy.*(hx(2:Nx,2:Ny,1:Nz)-hx(2:Nx,1:Ny-1,1:Nz));          

       
   Uz(2:Nx,2:Ny,1:Nz) = exp(-1i.*phiz(2:Nx,2:Ny,1:Nz));
   
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
 
hx(2:Nx,2:Ny-1,2:Nz-1) = (phiz(2:Nx,3:Ny,2:Nz-1)-phiz(2:Nx,2:Ny-1,2:Nz-1)...
             -phiy(2:Nx,2:Ny-1,3:Nz)+phiy(2:Nx,2:Ny-1,2:Nz-1))/dydz;
   

  hy(2:Nx-1,2:Ny,2:Nz-1) = (phix(2:Nx-1,2:Ny,3:Nz)-phix(2:Nx-1,2:Ny,2:Nz-1)...
            -phiz(3:Nx,2:Ny,2:Nz-1)+phiz(2:Nx-1,2:Ny,2:Nz-1))/dzdx;
           
   
  hz(2:Nx-1,2:Ny-1,2:Nz) = (phiy(3:Nx,2:Ny-1,2:Nz)-phiy(2:Nx-1,2:Ny-1,2:Nz)...
             -phix(2:Nx-1,3:Ny,2:Nz)+phix(2:Nx-1,2:Ny-1,2:Nz))/dxdy;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
 F(x1,y1+1:y2,z1+1:z2) = Ux(x1,y1+1:y2,z1+1:z2).*F(x1+1,y1+1:y2,z1+1:z2); %Check
 F(x2+1,y1+1:y2,z1+1:z2) = conj(Ux(x2,y1+1:y2,z1+1:z2)).*F(x2,y1+1:y2,z1+1:z2); %check
 
 F(x1+1:x2,y1,z1+1:z2) = Uy(x1+1:x2,y1,z1+1:z2).*F(x1+1:x2,y1+1,z1+1:z2);  %check
 F(x1+1:x2,y2+1,z1+1:z2) = conj(Uy(x1+1:x2,y2,z1+1:z2)).*F(x1+1:x2,y2,z1+1:z2);  %check
 
 F(x1+1:x2,y1+1:y2,z1) = Uz(x1+1:x2,y1+1:y2,z1).*F(x1+1:x2,y1+1:y2,z1+1);%check
 F(x1+1:x2,y1+1:y2,z2+1) = conj(Uz(x1+1:x2,y1+1:y2,z2)).*F(x1+1:x2,y1+1:y2,z2); %check
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
  hx(1,1:Ny,1:Nz)= 0.0;
  hx(Nx+1,1:Ny,1:Nz) = 0.0;  % estos campos deben revisarsen.
  hx(2:Nx,1,1:Nz)  = 0.0;
  hx(2:Nx,Ny,1:Nz) = 0.0;
  hx(2:Nx,2:Ny-1,1)  = 0.0;
  hx(2:Nx,2:Ny-1,Nz) = 0.0;
 
 
  hy(1:Nx,1,1:Nz)    = 0.0;
  hy(1:Nx,Ny+1,1:Nz) = 0.0;
  hy(1:Nx,2:Ny,1)  = 0.0;
  hy(1:Nx,2:Ny,Nz) = 0.0;
  hy(1,2:Ny,2:Nz-1)  = 0.0;
  hy(Nx,2:Ny,2:Nz-1) = 0.0;
 
 
  hz(1:Nx,1:Ny,1)    = H(p);
  hz(1:Nx,1:Ny,Nz) = H(p);
 
  hz(1,1:Ny,1:Nz)  = H(p);
  hz(Nx,1:Ny,1:Nz) = H(p);
 
  hz(2:Nx-1,1,1:Nz)  = H(p);
  hz(2:Nx-1,Ny,1:Nz) = H(p);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
   G(x1:x2+1,y1:y2+1,z1:z2+1) = F(x1:x2+1,y1:y2+1,z1:z2+1);
 
   thetax = phix;
   Vx= Ux;  
 
    thetay = phiy;
    Vy= Uy;
 
    thetaz = phiz;
    Vz= Uz;

    l = l+1;
     
     
 end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%        
F(x1,y1,z1) = 0.5.*(F(x1+1,y1,z1)+F(x1,y1,z1+1));
F(x1,y1,z1) = 0.5.*(F(x1,y1+1,z1)+F(x1,y1,z1+1));
F(x1,y1,z1) = 0.5.*(F(x1+1,y1,z1)+F(x1,y1+1,z1));%esta Izquierda abajo/frente

F(x1,y1,z2+1) = 0.5.*(F(x1,y1,z2)+F(x1+1,y1,z2+1));
F(x1,y1,z2+1) = 0.5.*(F(x1+1,y1,z2+1)+F(x1,y1+1,z2+1));%esta Izquierda arriba/frente
F(x1,y1,z2+1) = 0.5.*(F(x1,y1,z2)+F(x1,y1+1,z2+1));

F(x2+1,y1,z1) = 0.5.*(F(x2,y1,z1)+F(x2+1,y1,z1+1));
F(x2+1,y1,z1) = 0.5.*(F(x2+1,y1+1,z1)+F(x2+1,y1,z1+1));
F(x2+1,y1,z1) = 0.5.*(F(x2,y1,z1)+F(x2+1,y1+1,z1));%esta Derecha abajo/frente

F(x2+1,y1,z2+1) = 0.5.*(F(x2+1,y1,z2+1)+F(x2+1,y1,z2+1));
F(x2+1,y1,z2+1) = 0.5.*(F(x2+1,y1+1,z2+1)+F(x2+1,y1,z2));
F(x2+1,y1,z2+1) = 0.5.*(F(x2,y1,z2+1)+F(x2+1,y1+1,z2+1));%esta Derecha Arriba/frente

F(x1,y2+1,z2+1) = 0.5.*(F(x1,y2,z2+1)+F(x1,y2+1,z2));
F(x1,y2+1,z2+1) = 0.5.*(F(x1,y2,z2+1)+F(x1+1,y2+1,z2+1));%esta Izquierda Arriba/atras
F(x1,y2+1,z2+1) = 0.5.*(F(x1+1,y2+1,z2+1)+F(x1,y2+1,z2));

F(x2+1,y2+1,z2+1) = 0.5.*(F(x2+1,y2+1,z2)+F(x2+1,y2,z2+1));
F(x2+1,y2+1,z2+1) = 0.5.*(F(x2+1,y2+1,z2)+F(x2,y2+1,z2+1));
F(x2+1,y2+1,z2+1) = 0.5.*(F(x2,y2+1,z2+1)+F(x2+1,y2,z2+1));%esta Derecha Arriba/atras

F(x1,y2+1,z1) = 0.5.*(F(x1,y2,z1)+F(x1+1,y2+1,z1)); %esta  Izquierda Abajo/atras
F(x1,y2+1,z1) = 0.5.*(F(x1,y2,z1)+F(x1,y2+1,z1+1));
F(x1,y2+1,z1) = 0.5.*(F(x1+1,y2+1,z1)+F(x1,y2+1,z1+1));

F(x2+1,y2+1,z1) = 0.5.*(F(x2+1,y2,z1)+F(x2,y2+1,z1));
F(x2+1,y2+1,z1) = 0.5.*(F(x2+1,y2,z1)+F(x2+1,y2+1,z1+1));
F(x2+1,y2+1,z1) = 0.5.*(F(x2+1,y2,z1)+F(x2,y2+1,z1));  %Esta Dercha Abajo/atras

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
%F(x1,y1,z1:z2+1) = 0.5.*(F(x1+1,y1,z1:z2+1)+F(x1,y1+1,z1:z2+1));
%F(x2+1,y1,z1:z2+1) = 0.5.*(F(x2,y1,z1:z2+1)+F(x2+1,y1+1,z1:z2+1));
%F(x1,y2+1,z1:z2+1) = 0.5.*(F(x1,y2,z1:z2+1)+F(x1+1,y2+1,z1:z2+1));
%F(x2+1,y2+1,z1:z2+1) = 0.5.*(F(x2,y2+1,z1:z2+1)+ F(x2+1,y2,z1:z2+1));

%F(x1:x2+1,y1,z1) = 0.5.*(F(x1:x2+1,y1+1,z1)+F(x1:x2+1,y1,z1+1));
%F(x1:x2+1,y2+1,z1) = 0.5.*(F(x1:x2+1,y2,z1)+ F(x1:x2+1,y2+1,z1+1));
%F(x1:x2+1,y1,z2+1) = 0.5.*(F(x1:x2+1,y1,z2)+F(x1:x2+1,y1+1,z2+1));
%F(x1:x2+1,y2+1,z2+1) = 0.5.*(F(x1:x2+1,y2+1,z2)+F(x1:x2+1,y2,z2+1));

%F(x1,y1:y2+1,z1) = 0.5.*(F(x1+1,y1:y2+1,z1)+F(x1,y1:y2+1,z1+1));
%F(x2+1,y1:y2+1,z1) = 0.5.*(F(x2,y1:y2+1,z1)+F(x2+1,y1:y2+1,z1+1));  
%F(x1,y1:y2+1,z2+1) = 0.5.*(F(x1,y1:y2+1,z2)+F(x1+1,y1:y2+1,z2+1));  
%F(x2+1,y1:y2+1,z2+1) = 0.5.*(F(x2+1,y1:y2+1,z2)+F(x2,y1:y2+1,z2+1));  
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
Cooper1= abs(F);
diff = 0.0;
for  k = z1:z2+1
  for j = y1:y2+1
for i = x1:x2+1
dif = abs(Cooper1(i,j,k)-Cooper0(i,j,k));
Cooper0(i,j,k) = Cooper1(i,j,k);
if (dif>diff)
   diff = dif;
end
  end
end
end

diffh = 0.0;
for  k  = 1:Nz+1
  for  j = 1:Ny
 for  i = 1:Nx
difh = abs(hz(i,j,k)-fieldOld(i,j,k));
fieldOld(i,j,k) = hz(i,j,k);
if (difh>diffh)
    diffh = difh;
end
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
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%        
d = log(abs(F));
d2= F;
d3= abs(F).*abs(F);
d4= abs(F);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
phase = imag(log(F));
aJx(1:Nx,1:Ny,2:Nz) = 0.5.*currentx.*(Qx(1:Nx,1:Ny,2:Nz)+Qx(1:Nx,2:Ny+1,2:Nz));
aJy(1:Nx,1:Ny,2:Nz) = 0.5.*currenty.*(Qy(1:Nx,1:Ny,2:Nz)+Qy(2:Nx+1,1:Ny,2:Nz));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
fluxNew = 0.0;
for k = z1:z2
for j = y1:y2
for i = x1:x2
fluxNew = hz(i,j,k)+fluxNew; %hz(i,j,k+1)+
end
end
end
Bz      = fluxNew/jxjyjz;
aMgzt   = H(p)-Bz;
       
    Magt2(p,1) = H(p);
    Magt2(p,2) = aMgzt;  
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
energyC = 0.0;
for k = z1+1:z2
for  j = y1+1:y2
for  i = x1+1:x2
aa      = abs(Ux(i,j,k)*d2(i+1,j,k)-d2(i,j,k))/dx;
energyC = energyC+aa*aa;
aa      = abs(Uy(i,j,k)*d2(i,j+1,k)-d2(i,j,k))/dy;
energyC = energyC+aa*aa;
aa      = abs(Uz(i,j,k)*d2(i,j,k+1)-d2(i,j,k))/dz;
energyC = energyC+aa*aa;
end
end
end

energyC = CenergyC*energyC;

energyCd=0.0;

for k = z1+1:z2
    for j = y1+1:y2
      for i = x1+1:x2
          energyCd=energyCd+d4(i,j,k)*(0.5*d4(i,j,k)-1);
      end
    end
end

energyCd =CenergyCd*energyCd;



energyF = 0.0;
  for k = z1:z2
    for j = y1:y2
      for i = x1:x2
         aa      = hz(i,j,k)-H(p);  
         energyF = energyF+aa*aa;
      end
   end
  end

 
  for k = z1:z2
    for j = y1:y2
      for i = x1:x2
         aa      = hy(i,j,k);  
         energyF = energyF+aa*aa;
      end
   end
  end
 

  for k = z1:z2
    for j = y1:y2
      for i = x1:x2
         aa      = hx(i,j,k);  
         energyF = energyF+aa*aa;
      end
   end
end
 
energyF=CenergyF*energyF;
energy=energyF+energyC+energyCd;

energy2(p,1)=H(p);
energy2(p,2) = energy;% energy
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%      
subplot(2,2,2);
plot(energy2(:,1),energy2(:,2),'LineWidth',2);

subplot(2,2,1);
plot(Magt2(:,1),Magt2(:,2),'LineWidth',2);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    

    dir = num2str(H(p));

    mkdir('output/psi',dir);

    mkdir('output/field/',dir);

    mkdir('output/phase/',dir);
   
    mkdir('output/currentsx/',dir);
  
    mkdir('output/currentsy/',dir);
    

    file = strcat('output/psi/',dir,'/d.mat');

    save(file,'d');
    
    file = strcat('output/psi/',dir,'/d4.mat');

    save(file,'d4');
   
    file = strcat('output/currentsx/',dir,'/aJx.mat');

    save(file,'aJx');
    
    file = strcat('output/currentsy/',dir,'/aJy.mat');

    save(file,'aJy');
   
    file = strcat('output/field/',dir,'/hz.mat');

    save(file,'hz');

    file = strcat('output/phase/',dir,'/phase.mat');

    save(file,'phase');
   
   
    p = p+1;

end
 
 
 
