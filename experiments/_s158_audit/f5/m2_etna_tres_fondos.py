# -*- coding: utf-8 -*-
"""F5, medicion 2. En la unica pasada con resultado publicado de MIROVA (Etna 2023-05-19 00:54, NOAA-20, matriz de
ejemplo del OSF zm62w): sobre LOS MISMOS 5 pixeles que alerta el oraculo, el VRP con tres fondos.

  MIROVA  fondo del codigo (oraculo: dilatacion + interpolacion lineal, sin recorte)
  D       brazo D de D25: media de los vecinos no alertados de la 3x3 (radiancia), sin recorte
  K~      APROXIMACION de nuestro fondo de VIIRS 750 en K: Planck de la MEDIANA de la BT de M13 en el anillo de 5 a 25 km
          del centro de la grilla (sin los alertados), con recorte dL >= 0 por pixel. Es una aproximacion: el anillo de
          produccion se arma sobre el barrido nativo, no sobre la grilla remuestreada, y compute_bg_stats tiene filtros
          que aqui no se replican (pipeline/detection_context.py:1042).

Pregunta del instrumento de D25: en el unico caso con verdad de MIROVA, ¿el brazo que la metrica M premiaria por
"acercarse a MIROVA" es el que mas se parece al fondo del codigo? Si K~ y D quedan del mismo lado de MIROVA, M mide
la direccion correcta; si D se pasa, M premia una subida que el codigo no hace.
Instrumento 1: si el oraculo estuviera roto, el VRP MIROVA no daria 9,88 MW (OSF 9,8895). Instrumento 2: el recorte
a cero no cambia Etna (todos los dL > 0), se imprime.
"""
import io, sys
from pathlib import Path
import numpy as np
from scipy.io import loadmat

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s158_oraculo_mirova"))
import mirova_v750 as O  # noqa: E402

S = loadmat(str(RAIZ / "experiments" / "_s158_d17_diseno" / "osf_codigo_mirova" / "Example" / "VIIRS750_example.mat"))
m13, m15, box = (np.asarray(S[k], dtype=float) for k in ("ZI_M13", "ZI_M15", "BOX"))
dayflag = float(np.squeeze(S["dayflag"]))
sg = O.sunglint_angle(float(np.squeeze(S["sat_zen"])), float(np.squeeze(S["sun_zen"])),
                      float(np.squeeze(S["sat_azi"])), float(np.squeeze(S["sun_azi"])))
alert = O.hotspot_detection(m13, m15, box, dayflag, sg)
alert = np.asarray(alert[0] if isinstance(alert, tuple) else alert, dtype=int).ravel()
vrp_m, npix, dl_m, bk, lh, lb = O.vrp(m13, alert)
print("grilla", m13.shape, "| dayflag", dayflag, "| sunglint %.1f" % sg, "| alertas", npix)
print("MIROVA (oraculo): VRP %.4f MW  L_hot %.6f  L_bk %.6f" % (vrp_m, lh, lb))

flat = m13.ravel(order="F")
es = np.zeros(flat.size, bool); es[alert] = True; es2 = es.reshape(m13.shape, order="F")
filas, cols = np.nonzero(es2)
# D: media de los 8 vecinos no alertados (radiancia)
bk_d = []
for f, c in zip(filas, cols):
    v = [m13[i, j] for i in range(f - 1, f + 2) for j in range(c - 1, c + 2)
         if 0 <= i < m13.shape[0] and 0 <= j < m13.shape[1] and not es2[i, j] and np.isfinite(m13[i, j])]
    bk_d.append(np.mean(v))
bk_d = np.array(bk_d)
lhot = m13[filas, cols]
coef = O.MIR_COEFFICIENT * O.PIXEL_AREA_KM2 / 1e6
vrp_d = (lhot - bk_d).sum() * coef
# K~: anillo de 5 a 25 km del centro de la grilla (celdas de 0,75 km), mediana de BT de M13
n0, n1 = m13.shape
ci, cj = (n0 - 1) / 2.0, (n1 - 1) / 2.0
I, J = np.indices(m13.shape)
dist = 0.75 * np.hypot(I - ci, J - cj)
anillo = (dist >= 5) & (dist <= 25) & ~es2 & np.isfinite(m13)
bt13 = O.radiance_to_temperature(m13, 4.05)
t_bg = float(np.nanmedian(bt13[anillo]))
l_bg = float(O.temperature_to_radiance(np.array(t_bg), 4.05))
dl_k = np.maximum(lhot - l_bg, 0)
vrp_k = dl_k.sum() * coef
print("D  (media 8 vecinos no alertados): VRP %.4f MW  (%+.2f %% contra MIROVA)  L_bk por pixel %s" % (
    vrp_d, 100 * (vrp_d / vrp_m - 1), np.round(bk_d, 4)))
print("K~ (mediana del anillo 5-25 km, n=%d, T_bg %.2f K, L_bg %.4f): VRP %.4f MW  (%+.2f %% contra MIROVA); pixeles con dL<0 recortados: %d" % (
    int(anillo.sum()), t_bg, l_bg, vrp_k, 100 * (vrp_k / vrp_m - 1), int((lhot - l_bg < 0).sum())))
print("L_bk MIROVA por pixel:", np.round(bk.ravel(order="F")[alert], 4), "| L_hot:", np.round(lhot, 4))
print("d de la metrica M si 'MIROVA' fuera el VRP del oraculo: d = |log10(D/M)| - |log10(K~/M)| = %.4f" % (
    abs(np.log10(vrp_d / vrp_m)) - abs(np.log10(vrp_k / vrp_m))))
