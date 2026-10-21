% O1 (S159): corre MIROVA_VIIRS750_hotspot_detection.m (original o una copia mutada) en GNU Octave 11.3
% sobre todas las escenas de entradas.mat. Uso (desde esta carpeta):
%   octave-cli --no-gui --eval "MDIR='<carpeta con el .m>'; SALIDA='salida_xxx.mat'; correr_octave"
% Sin shims: la detección sólo necesita colfilt (paquete image de Octave Forge, que trae el instalador),
% mean/std con 'omitnan', polyfit, polyval, find, validateattributes, narginchk.
% Guarda la lista de alertas de cada escena TAL CUAL la devuelve el .m (orden y duplicados incluidos).
pkg load image
addpath(MDIR);
w = which('MIROVA_VIIRS750_hotspot_detection');
printf('usando: %s\n', w);
S = load('entradas.mat');
K = size(S.M13, 3);
ALERTAS = [];      % concatenadas
OFFSET = zeros(K, 1); NALERT = zeros(K, 1); NUNICO = zeros(K, 1);
t0 = tic;
for k = 1:K
  a = MIROVA_VIIRS750_hotspot_detection(S.M13(:,:,k), S.M15(:,:,k), S.BOX(:,:,k), S.DAY(k), S.SG(k));
  a = a(:);
  OFFSET(k) = numel(ALERTAS);
  NALERT(k) = numel(a);
  NUNICO(k) = numel(unique(a));
  ALERTAS = [ALERTAS; a];
end
printf('escenas %d, con alerta %d, alertas totales %d, escenas con duplicados %d, %.1f s\n', ...
       K, sum(NALERT > 0), numel(ALERTAS), sum(NALERT ~= NUNICO), toc(t0));
% Etna: Tot_Lmir_hot del OSF v2.5 = 1.965342180
a1 = ALERTAS(OFFSET(1)+1 : OFFSET(1)+NALERT(1));
m13 = S.M13(:,:,1);
printf('Etna: npix %d, indices %s, Tot_Lmir_hot %.9f\n', numel(a1), mat2str(a1'), sum(m13(a1)));
save('-v7', SALIDA, 'ALERTAS', 'OFFSET', 'NALERT', 'NUNICO', 'w');
rmpath(MDIR);
