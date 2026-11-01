# -*- coding: utf-8 -*-
"""A61 (S162): que hace `_interp_geo` de `pipeline/process_modis.py` con (a) el desfase de indice de la grilla de
5 km y (b) un bloque de relleno -999, medido sobre una grilla SINTETICA (sin HDF: no hay granulos en disco y bajar
uno exige credenciales).

Las dos preguntas del instrumento:
1. Si `_interp_geo` estuviera bien (centrada en el pixel 5i+2 y enmascarando el relleno), ¿esto lo veria? Si: el
   error de indice daria 0 en todas las columnas y ningun pixel fino quedaria con valor intermedio entre el real y
   -999. Control positivo: una interpolacion de referencia hecha a mano con el offset correcto da error 0.
2. Si el instrumento estuviera muerto, ¿se veria distinto? Si: la funcion importada es la de produccion (se imprime
   su archivo y su hash); si no se importara, el script revienta.

Grilla sintetica: lat = linea fina, lon = frame fino (unidades de pixel), muestreada en (5i+2, 5j+2) como dice la
especificacion de MOD021KM para el SDS Latitude/Longitude de 5 km (406 x 271 para 2030 x 1354). Asi el valor
interpolado en un pixel fino menos su indice real ES el error de indice en pixeles.
"""
import hashlib
import inspect
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from pipeline import process_modis as pm  # noqa: E402

src = inspect.getsource(pm._interp_geo)
print("funcion:", inspect.getsourcefile(pm._interp_geo), "sha256 fuente:", hashlib.sha256(src.encode()).hexdigest()[:16])
NL, NS = 2030, 1354
lin_f = np.arange(NL, dtype=np.float32)[:, None] * np.ones((1, NS), np.float32)
fra_f = np.ones((NL, 1), np.float32) * np.arange(NS, dtype=np.float32)[None, :]
# muestreo de la grilla de 5 km en el centro de cada bloque 5x5: lineas 2,7,...,2027 ; frames 2,7,...,1352
li, fi = np.arange(2, NL, 5), np.arange(2, NS, 5)
print("grilla gruesa sintetica:", (len(li), len(fi)), "(esperado 406 x 271)")
lin_c, fra_c = lin_f[np.ix_(li, fi)], fra_f[np.ix_(li, fi)]
lin_i, fra_i = pm._interp_geo(lin_c, NL, NS), pm._interp_geo(fra_c, NL, NS)
e_lin, e_fra = lin_i - lin_f, fra_i - fra_f

print("\n== (a) error de indice de `_interp_geo` (valor interpolado menos indice real), en pixeles")
print("   a lo largo del barrido (frame): frame 0 -> %+.2f | frame 902 -> %+.2f | frame 1353 -> %+.2f | min %+.2f max %+.2f" % (
    e_fra[1000, 0], e_fra[1000, 902], e_fra[1000, 1353], e_fra.min(), e_fra.max()))
print("   a lo largo de la traza (linea): linea 0 -> %+.2f | linea 1014 -> %+.2f | linea 2029 -> %+.2f | min %+.2f max %+.2f" % (
    e_lin[0, 600], e_lin[1014, 600], e_lin[2029, 600], e_lin.min(), e_lin.max()))
cero = np.argmin(np.abs(e_fra[1000, :]))
print("   frame donde el error cruza 0:", int(cero), "| lectura: en el frame 0 el pixel recibe la posicion del pixel",
      "%.1f frames hacia el nadir; en el 1353, la del pixel %.1f frames hacia el nadir" % (e_fra[1000, 0], -e_fra[1000, 1353]))

# control positivo: la interpolacion correcta (offset 2) da error ~0
from scipy.interpolate import RegularGridInterpolator  # noqa: E402
# la interpolacion correcta: nodo grueso (i, j) en el pixel fino (5i+2, 5j+2), lineal, con extrapolacion lineal en el borde
rgi = RegularGridInterpolator((li.astype(np.float64), fi.astype(np.float64)), fra_c.astype(np.float64),
                              method="linear", bounds_error=False, fill_value=None)
Y, X = np.meshgrid(np.arange(NL, dtype=np.float64), np.arange(NS, dtype=np.float64), indexing="ij")
fra_ok = rgi(np.stack([Y.ravel(), X.ravel()], axis=1)).reshape(NL, NS)
e_ok = fra_ok - fra_f
print("   control positivo (interpolacion con el nodo grueso en 5i+2, extrapolacion lineal en el borde): error max |%.4f| px" % np.abs(e_ok).max(),
      "| frame 0..3:", np.round(e_ok[1000, :4], 3).tolist(), "| frame 1350..1353:", np.round(e_ok[1000, -4:], 3).tolist())

print("\n== (b) bloque de relleno -999 en la grilla gruesa")
lat_c = (-23.0 - 0.009 * lin_c).astype(np.float32)    # ~1 km por linea, latitud plausible
lat_c_fill = lat_c.copy()
# bloque de relleno: 30 lineas gruesas (150 finas) en todo el ancho, como un tramo sin efemerides
lat_c_fill[100:130, :] = -999.0
lat_fill = pm._interp_geo(lat_c_fill, NL, NS)
lat_ok = pm._interp_geo(lat_c, NL, NS)
exacto = np.isclose(lat_fill, -999.0)
interm = (~exacto) & (np.abs(lat_fill - lat_ok) > 1e-3)
print("   pixeles finos con -999 exacto: %d | pixeles finos CONTAMINADOS (valor entre el real y -999): %d" % (exacto.sum(), interm.sum()))
filas_int = np.flatnonzero(interm.any(axis=1))
print("   lineas finas contaminadas: %d, de la %d a la %d (el bloque grueso 100:130 cubre las finas %d a %d)" % (
    len(filas_int), filas_int.min(), filas_int.max(), 100 * 5 + 2, 129 * 5 + 2))
ej = lat_fill[filas_int[:6], 600]
print("   ejemplo de latitudes contaminadas (columna 600):", np.round(ej, 2).tolist())
print("   lectura: una latitud de -400 o -800 no cae en ningun ROI, pero el pixel existe con un valor absurdo y nadie lo enmascara aguas abajo:",
      "grep -n -- '-999' pipeline/process_modis.py y grep -n 'isfinite(lat' dan 0 lineas (verificado aparte).")
print("   nota: si el relleno de la grilla de 5 km del L1B fuera NaN en vez de -999, `zoom` propagaria NaN a los vecinos (mismo alcance de 1 celda gruesa).")
