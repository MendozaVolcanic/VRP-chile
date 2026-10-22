%% O2 (S159): correr el codigo de MIROVA en MATLAB Online sobre las matrices de VRP Chile
% Corre MIROVA_VIIRS750_hotspot_detection.m y MIROVA_VIIRS750_VRP.m (copias sin cambios del OSF, licencia MIT)
% sobre las 311 escenas de entradas_o2.mat y guarda en resultado_o2.mat, por escena: la lista de alertas tal como
% la devuelve el .m, el VRP, npix, deltaL_MIR y la suma del fondo bajo las alertas. Para Etna y las 190 escenas
% chilenas guarda ademas la matriz de fondo ZI_M13bk completa. Esto fija lo que Octave no puede: fillmissing2.
% Uso: abrir esta carpeta en MATLAB Online y ejecutar  correr_o2
clear; clc;
aqui = fileparts(mfilename('fullpath'));
cd(aqui);
fprintf('MATLAB %s\n', version);
fprintf('fillmissing2: %s\n', which('fillmissing2'));
fprintf('colfilt: %s\n', which('colfilt'));
assert(~isempty(which('fillmissing2')), 'Falta fillmissing2 (requiere R2024a o posterior).');
assert(~isempty(which('colfilt')), 'Falta la Image Processing Toolbox.');
S = load('entradas_o2.mat');
K = size(S.M13, 3);
ALERTAS = cell(K, 1); VRP = NaN(K, 1); NPIX = zeros(K, 1); DL = NaN(K, 1);
LHOT = NaN(K, 1); LBK = NaN(K, 1); BK = cell(K, 1);
t0 = tic;
for k = 1:K
    m13 = S.M13(:, :, k);
    a = MIROVA_VIIRS750_hotspot_detection(m13, S.M15(:, :, k), S.BOX(:, :, k), S.DAY(k), S.SG(k));
    ALERTAS{k} = a(:);
    if ~isempty(a)
        [VRP(k), NPIX(k), DL(k), bk] = MIROVA_VIIRS750_VRP(m13, a);
        LHOT(k) = sum(m13(a), 'omitnan');
        LBK(k) = sum(bk(a), 'omitnan');
        if k <= 191
            BK{k} = bk;
        end
    end
end
fprintf('%d escenas, %d con alerta, %.1f s\n', K, sum(NPIX > 0), toc(t0));
fprintf('Etna: npix %d, Tot_Lmir_hot %.9f, Tot_Lmir_bk %.9f, VRP %.1f W\n', NPIX(1), LHOT(1), LBK(1), VRP(1) * 1e6);
fprintf('      (OSF v2.5: npix 5, Tot_Lmir_hot 1.965342180, Tot_Lmir_bk 1.072886152, VRP 9889528.4 W)\n');
version_matlab = version;
save('resultado_o2.mat', 'ALERTAS', 'VRP', 'NPIX', 'DL', 'LHOT', 'LBK', 'BK', 'version_matlab', '-v7');
fprintf('Listo: resultado_o2.mat\n');
