%% O2-375 (S163): el fondo del VRP de MIROVA en MATLAB sobre las escenas VIIRS 375 de 1 a 4 pixeles de VRP Chile
% Corre MIROVA_VIIRS750_VRP.m (copia sin cambios del OSF, licencia MIT) sobre las K escenas de entradas_v375.mat:
% radiancia I4 remuestreada a la grilla de 134 x 134 de MIROVA (RAD) y las alertas que dio el port de VRP Chile (ALE,
% indices lineales de MATLAB, NAL de ellos por escena). El fondo no depende del sensor; el coeficiente si: el .m usa el
% de VIIRS 750 y VRP Chile lo reescala al leer (VRP_375 = DL x 1,80e7 x 0,140625 / 1e6). Por eso se guarda DL.
% Control: la escena de Etna de O2 (ETNA_*), re-detectada con MIROVA_VIIRS750_hotspot_detection.m sin cambios; tiene
% que dar Tot_Lmir_bk 1.072886152 como en el OSF v2.5.
% Guarda en resultado_v375.mat, por escena: VRP (el del .m, con el coeficiente de 750), NPIX, DL, LHOT, LBK y la matriz
% de fondo BK completa (134 x 134 x K, single).
% Uso: abrir esta carpeta en MATLAB Online y ejecutar  correr_v375
clear; clc;
aqui = fileparts(mfilename('fullpath'));
cd(aqui);
fprintf('MATLAB %s\n', version);
fprintf('fillmissing2: %s\n', which('fillmissing2'));
fprintf('imdilate: %s\n', which('imdilate'));
assert(~isempty(which('fillmissing2')), 'Falta fillmissing2 (requiere R2024a o posterior).');
assert(~isempty(which('imdilate')), 'Falta la Image Processing Toolbox.');
S = load('entradas_v375.mat');
% control de Etna
a = MIROVA_VIIRS750_hotspot_detection(S.ETNA_M13, S.ETNA_M15, S.ETNA_BOX, S.ETNA_DAY, S.ETNA_SG);
[ev, en, ed, eb] = MIROVA_VIIRS750_VRP(S.ETNA_M13, a);
ETNA = struct('alertas', a(:), 'VRP', ev, 'NPIX', en, 'DL', ed, 'LHOT', sum(double(S.ETNA_M13(a)), 'omitnan'), ...
              'LBK', sum(eb(a), 'omitnan'));
fprintf('Etna: npix %d, Tot_Lmir_hot %.9f, Tot_Lmir_bk %.9f, VRP %.1f W\n', en, ETNA.LHOT, ETNA.LBK, ev * 1e6);
fprintf('      (OSF v2.5: npix 5, Tot_Lmir_hot 1.965342180, Tot_Lmir_bk 1.072886152, VRP 9889528.4 W)\n');
K = size(S.RAD, 3);
VRP = NaN(K, 1); NPIX = zeros(K, 1); DL = NaN(K, 1); LHOT = NaN(K, 1); LBK = NaN(K, 1);
BK = NaN(size(S.RAD), 'single');
t0 = tic;
for k = 1:K
    rad = double(S.RAD(:, :, k));
    alerta = double(S.ALE(k, 1:S.NAL(k)));
    [VRP(k), NPIX(k), DL(k), bk] = MIROVA_VIIRS750_VRP(rad, alerta);
    LHOT(k) = sum(rad(alerta), 'omitnan');
    LBK(k) = sum(bk(alerta), 'omitnan');
    BK(:, :, k) = single(bk);
end
fprintf('%d escenas, %.1f s; NPIX 1 a 4: %d de %d\n', K, toc(t0), sum(NPIX >= 1 & NPIX <= 4), K);
version_matlab = version;
save('resultado_v375.mat', 'VRP', 'NPIX', 'DL', 'LHOT', 'LBK', 'BK', 'ETNA', 'version_matlab', '-v7');
fprintf('Listo: resultado_v375.mat\n');
