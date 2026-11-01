% V0a (verificador de F6-5): que hace MIROVA_VIIRS750_VRP con un alert vacio 0x0 (escena rechazada, H:81) y
% con un vacio 0x1 (escena aceptada sin alertas: find() sobre una matriz devuelve 0x1). INTERPRETE: GNU Octave,
% NO MATLAB; validateattributes de Octave puede diferir del de MATLAB en el trato de empties (el informe lo declara).
% Pregunta 1: si el 0x0 pasara la validacion, se imprime NaN sin error. Pregunta 2 (control): un indice fuera de
% rango debe dar el error MIROVA:InvalidAlertIndex (asi se ve que la funcion si corre y si valida).
pkg load image
addpath('C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova');
S = load('C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat');
printf('size([]) = %dx%d ; size(find(zeros(3))) = %dx%d ; size([[];[];[]]) = %dx%d ; size([zeros(0,1);zeros(0,1)]) = %dx%d\n', ...
    size([]), size(find(zeros(3))), size([[];[];[]]), size([zeros(0,1);zeros(0,1)]));
printf('isvector([]) = %d ; isvector(zeros(0,1)) = %d\n', isvector([]), isvector(zeros(0,1)));
casos = {[], zeros(0,1)};
nombres = {'0x0 (escena rechazada, H:81)', '0x1 (sin alertas en escena aceptada)'};
for i = 1:2
  try
    [v, n, dl, bk] = MIROVA_VIIRS750_VRP(S.ZI_M13, casos{i});
    printf('%s -> VRP_MW = %g, npix = %d, deltaL = %g, size(bk) = %dx%d (SIN ERROR)\n', nombres{i}, v, n, dl, size(bk));
  catch err
    printf('%s -> ERROR: %s | %s\n', nombres{i}, err.identifier, err.message);
  end
end
% validateattributes aislado, para separar el trato del empty del resto de la funcion
try
  validateattributes([], {'numeric'}, {'real','vector','integer','positive'}, 'x', 'alert', 2);
  printf('validateattributes([] ... vector) PASA en Octave\n');
catch err
  printf('validateattributes([] ... vector) ERROR en Octave: %s\n', err.message);
end
try
  validateattributes(zeros(0,1), {'numeric'}, {'real','vector','integer','positive'}, 'x', 'alert', 2);
  printf('validateattributes(zeros(0,1) ... vector) PASA en Octave\n');
catch err
  printf('validateattributes(zeros(0,1) ... vector) ERROR en Octave: %s\n', err.message);
end
% control positivo: indice fuera de rango debe fallar con el error propio de la funcion
try
  MIROVA_VIIRS750_VRP(S.ZI_M13, numel(S.ZI_M13) + 1);
  printf('CONTROL: indice fuera de rango NO fallo (instrumento roto)\n');
catch err
  printf('CONTROL: indice fuera de rango -> %s (esperado MIROVA:InvalidAlertIndex)\n', err.identifier);
end
% y el camino normal del ejemplo, para ver que la funcion corre en este interprete
cosS = cosd(S.sat_zen).*cosd(S.sun_zen) - sind(S.sat_zen).*sind(S.sun_zen).*cosd(S.sun_azi-S.sat_azi);
sg = acosd(max(-1, min(1, cosS)));
try
  alert = MIROVA_VIIRS750_hotspot_detection(S.ZI_M13, S.ZI_M15, S.BOX, S.dayflag, sg);
  printf('deteccion Etna en Octave: %d alertas, size %dx%d\n', numel(alert), size(alert));
  % escena rechazada por sun-glint: que devuelve la deteccion
  a2 = MIROVA_VIIRS750_hotspot_detection(S.ZI_M13, S.ZI_M15, S.BOX, S.dayflag, 5);
  printf('deteccion con sunglint=5 (rechazo): size(alert) = %dx%d\n', size(a2));
  % escena aceptada sin alertas: NTI plano (M13 = M15 en todas partes) -> ninguna alerta
  a3 = MIROVA_VIIRS750_hotspot_detection(S.ZI_M15, S.ZI_M15, S.BOX, S.dayflag, sg);
  printf('deteccion con M13 = M15 (sin alertas): size(alert) = %dx%d\n', size(a3));
  try
    [v3, n3] = MIROVA_VIIRS750_VRP(S.ZI_M13, a3);
    printf('VRP con ese alert -> %g, npix %d (SIN ERROR)\n', v3, n3);
  catch err
    printf('VRP con ese alert -> ERROR: %s\n', err.message);
  end
catch err
  printf('deteccion en Octave fallo: %s\n', err.message);
end
