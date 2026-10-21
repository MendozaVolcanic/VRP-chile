% O1 (S159): VRP con el .m ORIGINAL (MIROVA_VIIRS750_VRP.m) + shim de fillmissing2 (MODELO, ver el shim).
% Escenas: las 791 de entradas.mat (las que tienen alerta), con las alertas que dio el .m de detección en Octave.
pkg load image
addpath('C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova');
addpath('C:/vrp-trabajo/s159-pruebas/experiments/_s159/o1/shim_fillmissing2');
printf('fillmissing2 -> %s\n', which('fillmissing2'));
S = load('entradas.mat'); D = load('salida_original.mat');
K = size(S.M13,3); VRP = NaN(K,1); LHOT = NaN(K,1); LBK = NaN(K,1); NP = zeros(K,1);
for k = 1:K
  a = D.ALERTAS(D.OFFSET(k)+1 : D.OFFSET(k)+D.NALERT(k));
  if isempty(a), continue; end
  m13 = S.M13(:,:,k);
  [VRP(k), NP(k), dL, bk] = MIROVA_VIIRS750_VRP(m13, a);
  LHOT(k) = sum(m13(a)); LBK(k) = sum(bk(a));
end
printf('Etna: npix %d L_hot %.9f L_bk %.9f VRP %.1f W (OSF: L_bk 1.072886152, VRP 9889528.4 W)\n', NP(1), LHOT(1), LBK(1), VRP(1)*1e6);
save('-v7', 'salida_vrp_octave_shim.mat', 'VRP', 'LHOT', 'LBK', 'NP');
