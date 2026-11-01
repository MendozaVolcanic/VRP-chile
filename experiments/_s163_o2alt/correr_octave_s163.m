% S163 O2 alternativa: re-corre en Octave 11.3 la detección (.m original) y el VRP con el shim de S159,
% leyendo las entradas de S159 (sólo lectura) y escribiendo en esta carpeta. Sirve para comprobar que las salidas
% de S159 que usa este informe se reproducen hoy (pregunta 1 del instrumento: ¿mido lo mismo que S159 midió?).
pkg load image
O1 = 'C:/vrp-trabajo/s159-pruebas/experiments/_s159/o1';
MDIR = 'C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova';
addpath(MDIR); addpath([O1 '/shim_fillmissing2']);
printf('deteccion -> %s\nfillmissing2 -> %s\n', which('MIROVA_VIIRS750_hotspot_detection'), which('fillmissing2'));
S = load([O1 '/entradas.mat']);
K = size(S.M13, 3);
ALERTAS = []; OFFSET = zeros(K,1); NALERT = zeros(K,1);
VRP = NaN(K,1); LHOT = NaN(K,1); LBK = NaN(K,1); NP = zeros(K,1);
for k = 1:K
  a = MIROVA_VIIRS750_hotspot_detection(S.M13(:,:,k), S.M15(:,:,k), S.BOX(:,:,k), S.DAY(k), S.SG(k));
  a = a(:); OFFSET(k) = numel(ALERTAS); NALERT(k) = numel(a); ALERTAS = [ALERTAS; a];
  if isempty(a), continue; end
  m13 = S.M13(:,:,k);
  [VRP(k), NP(k), dL, bk] = MIROVA_VIIRS750_VRP(m13, a);
  LHOT(k) = sum(m13(a)); LBK(k) = sum(bk(a));
end
printf('escenas %d con alerta %d\n', K, sum(NALERT>0));
printf('Etna: npix %d L_hot %.9f L_bk %.9f VRP %.1f W\n', NP(1), LHOT(1), LBK(1), VRP(1)*1e6);
save('-v7', 'salida_octave_s163.mat', 'ALERTAS', 'OFFSET', 'NALERT', 'VRP', 'LHOT', 'LBK', 'NP');
