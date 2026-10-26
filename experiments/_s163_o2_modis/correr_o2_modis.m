%% O2 MODIS (S163): el fondo del VRP del codigo de MIROVA, en MATLAB, sobre escenas MODIS reales de 1 a 4 pixeles
% Corre MIROVA_VIIRS750_VRP.m (copia sin cambios del OSF, licencia MIT) sobre las escenas de entradas_o2_modis.mat,
% con la lista de alertas que decidio nuestro port (la deteccion ya esta validada contra MATLAB en S163). Guarda en
% resultado_o2_modis.mat, por escena: VRP (con el coeficiente de VIIRS 750 del .m; se reescala a MODIS con DL),
% NPIX, DL (delta L), LHOT (suma de la radiancia MIR bajo las alertas), LBK (suma del fondo bajo las alertas) y BK
% (la matriz de fondo completa). No agregues a la ruta ningun fillmissing2.m propio: el script imprime su ruta.
% Uso: abrir esta carpeta en MATLAB Online y ejecutar  correr_o2_modis
clear; clc;
aqui = fileparts(mfilename('fullpath'));
cd(aqui);
fprintf('MATLAB %s\n', version);
fprintf('fillmissing2: %s\n', which('fillmissing2'));
assert(~isempty(which('fillmissing2')), 'Falta fillmissing2 (requiere R2024a o posterior).');
S = load('entradas_o2_modis.mat');
K = size(S.M13, 3);
VRP = NaN(K, 1); NPIX = zeros(K, 1); DL = NaN(K, 1); LHOT = NaN(K, 1); LBK = NaN(K, 1); BK = cell(K, 1);
t0 = tic;
for k = 1:K
    m13 = S.M13(:, :, k);
    a = S.ALERTAS{k};
    [VRP(k), NPIX(k), DL(k), bk] = MIROVA_VIIRS750_VRP(m13, a);
    LHOT(k) = sum(m13(a), 'omitnan');
    LBK(k) = sum(bk(a), 'omitnan');
    BK{k} = bk;
end
fprintf('%d escenas, %.1f s; npix 1: %d, 2: %d, 3: %d, 4: %d\n', K, toc(t0), sum(NPIX == 1), sum(NPIX == 2), ...
        sum(NPIX == 3), sum(NPIX == 4));
version_matlab = version;
save('resultado_o2_modis.mat', 'VRP', 'NPIX', 'DL', 'LHOT', 'LBK', 'BK', 'version_matlab', '-v7');
fprintf('Listo: resultado_o2_modis.mat\n');
