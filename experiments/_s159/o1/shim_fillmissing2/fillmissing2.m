function B = fillmissing2(A, metodo)
% SHIM, NO es el fillmissing2 de MATLAB (Octave 11.3 no lo trae). MODELO declarado:
% interpolación lineal sobre la triangulación de Delaunay de Octave (griddata, Qhull) de los centros no faltantes,
% y vecino más cercano fuera de la envolvente convexa (misma convención que el segundo port). La diagonal que elige
% MATLAB en cada celda cocircular no la fija nadie (docs/AUDIT_S158_R2.md §2): este shim es UNA de esas elecciones.
% Lo que decide el .m de VRP (qué píxeles se quitan, la dilatación imdilate/strel del paquete image, el tamaño del
% núcleo 3/5/7, la suma y el coeficiente) sigue siendo el .m original.
  if ~strcmp(metodo, 'linear'), error('shim: sólo linear'); end
  [n, m] = size(A);
  [C, R] = meshgrid(1:m, 1:n);
  ok = isfinite(A);
  B = A;
  if all(ok(:)), return; end
  falta = ~ok;
  v = griddata(C(ok), R(ok), A(ok), C(falta), R(falta), 'linear');
  sinv = ~isfinite(v);
  if any(sinv)
    v(sinv) = griddata(C(ok), R(ok), A(ok), C(falta)(sinv), R(falta)(sinv), 'nearest');
  end
  B(falta) = v;
end
