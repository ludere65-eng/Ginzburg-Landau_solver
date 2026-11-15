function F = aplicar_suavizado_3d(F, estado, cfg)
% APLICAR_SUAVIZADO_3D Suaviza el parámetro de orden en los bordes.
% Permite al usuario elegir entre suavizar solo los 8 vértices, 
% las 12 aristas, o ambos.

    % Extraemos coordenadas para que el código sea idéntico al original
    x1 = estado.x1; x2 = estado.x2;
    y1 = estado.y1; y2 = estado.y2;
    z1 = estado.z1; z2 = estado.z2;

    % Opción 1: Suavizar las 12 aristas (Tu código comentado original)
    if strcmp(cfg.suavizado_bordes, '12_aristas') || strcmp(cfg.suavizado_bordes, 'ambos')
        % Aristas a lo largo del eje Z
        F(x1, y1, z1:z2+1) = 0.5 .* (F(x1+1, y1, z1:z2+1) + F(x1, y1+1, z1:z2+1));
        F(x2+1, y1, z1:z2+1) = 0.5 .* (F(x2, y1, z1:z2+1) + F(x2+1, y1+1, z1:z2+1));
        F(x1, y2+1, z1:z2+1) = 0.5 .* (F(x1, y2, z1:z2+1) + F(x1+1, y2+1, z1:z2+1));
        F(x2+1, y2+1, z1:z2+1) = 0.5 .* (F(x2, y2+1, z1:z2+1) + F(x2+1, y2, z1:z2+1));

        % Aristas a lo largo del eje X
        F(x1:x2+1, y1, z1) = 0.5 .* (F(x1:x2+1, y1+1, z1) + F(x1:x2+1, y1, z1+1));
        F(x1:x2+1, y2+1, z1) = 0.5 .* (F(x1:x2+1, y2, z1) + F(x1:x2+1, y2+1, z1+1));
        F(x1:x2+1, y1, z2+1) = 0.5 .* (F(x1:x2+1, y1, z2) + F(x1:x2+1, y1+1, z2+1));
        F(x1:x2+1, y2+1, z2+1) = 0.5 .* (F(x1:x2+1, y2+1, z2) + F(x1:x2+1, y2, z2+1));

        % Aristas a lo largo del eje Y
        F(x1, y1:y2+1, z1) = 0.5 .* (F(x1+1, y1:y2+1, z1) + F(x1, y1:y2+1, z1+1));
        F(x2+1, y1:y2+1, z1) = 0.5 .* (F(x2, y1:y2+1, z1) + F(x2+1, y1:y2+1, z1+1));  
        F(x1, y1:y2+1, z2+1) = 0.5 .* (F(x1, y1:y2+1, z2) + F(x1+1, y1:y2+1, z2+1));  
        F(x2+1, y1:y2+1, z2+1) = 0.5 .* (F(x2+1, y1:y2+1, z2) + F(x2, y1:y2+1, z2+1));  
    end

    % Opción 2: Suavizar los 8 vértices (Tu código activo original)
    if strcmp(cfg.suavizado_bordes, '8_vertices') || strcmp(cfg.suavizado_bordes, 'ambos')
        % Esquina Izquierda abajo/frente
        F(x1,y1,z1) = 0.5.*(F(x1+1,y1,z1)+F(x1,y1,z1+1));
        F(x1,y1,z1) = 0.5.*(F(x1,y1+1,z1)+F(x1,y1,z1+1));
        F(x1,y1,z1) = 0.5.*(F(x1+1,y1,z1)+F(x1,y1+1,z1));
        
        % Esquina Izquierda arriba/frente
        F(x1,y1,z2+1) = 0.5.*(F(x1,y1,z2)+F(x1+1,y1,z2+1));
        F(x1,y1,z2+1) = 0.5.*(F(x1+1,y1,z2+1)+F(x1,y1+1,z2+1));
        F(x1,y1,z2+1) = 0.5.*(F(x1,y1,z2)+F(x1,y1+1,z2+1));

        % Esquina Derecha abajo/frente
        F(x2+1,y1,z1) = 0.5.*(F(x2,y1,z1)+F(x2+1,y1,z1+1));
        F(x2+1,y1,z1) = 0.5.*(F(x2+1,y1+1,z1)+F(x2+1,y1,z1+1));
        F(x2+1,y1,z1) = 0.5.*(F(x2,y1,z1)+F(x2+1,y1+1,z1));

        % Esquina Derecha arriba/frente
        F(x2+1,y1,z2+1) = 0.5.*(F(x2+1,y1,z2+1)+F(x2+1,y1,z2+1)); % Nota original tuya
        F(x2+1,y1,z2+1) = 0.5.*(F(x2+1,y1+1,z2+1)+F(x2+1,y1,z2));
        F(x2+1,y1,z2+1) = 0.5.*(F(x2,y1,z2+1)+F(x2+1,y1+1,z2+1));

        % Esquina Izquierda arriba/atras
        F(x1,y2+1,z2+1) = 0.5.*(F(x1,y2,z2+1)+F(x1,y2+1,z2));
        F(x1,y2+1,z2+1) = 0.5.*(F(x1,y2,z2+1)+F(x1+1,y2+1,z2+1));
        F(x1,y2+1,z2+1) = 0.5.*(F(x1+1,y2+1,z2+1)+F(x1,y2+1,z2));

        % Esquina Derecha arriba/atras
        F(x2+1,y2+1,z2+1) = 0.5.*(F(x2+1,y2+1,z2)+F(x2+1,y2,z2+1));
        F(x2+1,y2+1,z2+1) = 0.5.*(F(x2+1,y2+1,z2)+F(x2,y2+1,z2+1));
        F(x2+1,y2+1,z2+1) = 0.5.*(F(x2,y2+1,z2+1)+F(x2+1,y2,z2+1));

        % Esquina Izquierda abajo/atras
        F(x1,y2+1,z1) = 0.5.*(F(x1,y2,z1)+F(x1+1,y2+1,z1)); 
        F(x1,y2+1,z1) = 0.5.*(F(x1,y2,z1)+F(x1,y2+1,z1+1));
        F(x1,y2+1,z1) = 0.5.*(F(x1+1,y2+1,z1)+F(x1,y2+1,z1+1));

        % Esquina Derecha abajo/atras
        F(x2+1,y2+1,z1) = 0.5.*(F(x2+1,y2,z1)+F(x2,y2+1,z1));
        F(x2+1,y2+1,z1) = 0.5.*(F(x2+1,y2,z1)+F(x2+1,y2+1,z1+1));
        F(x2+1,y2+1,z1) = 0.5.*(F(x2+1,y2,z1)+F(x2,y2+1,z1));  
    end
end