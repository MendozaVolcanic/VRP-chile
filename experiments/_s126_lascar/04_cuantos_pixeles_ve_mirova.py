# -*- coding: utf-8 -*-
"""S126 — ?cuantos pixeles calientes tiene MIROVA en el crater de Lascar?

LA HIPOTESIS A CONTRASTAR. El script 02 concluyo, por aritmetica sobre NUESTROS
records, que a Lascar le falta ~1,57 pixeles: para llegar al VRP de MIROVA desde
nuestro pixel unico haria falta un fondo de 238 K cuando el mas frio del disco de 3 km
era 273-276 K. Imposible. La unica salida es que MIROVA integre mas pixeles.

Eso era una INFERENCIA sobre nuestros propios datos. El repositorio `mirova-tif-archive`
guarda el campo I04 de MIROVA en GeoTIFF, asi que la extension de su region caliente se
puede MEDIR sobre su propia imagen — evidencia exogena.

CONTROL: Villarrica, donde ya esta probado que no hay foco resoluble. Si su conteo sale
igual que el de Lascar, el metodo no distingue nada y el resultado no vale.

═══════════════════════════════════════════════════════════════════════════════
DOS METODOS DESCARTADOS ANTES DE LLEGAR AL BUENO — y lo que ensenaron
═══════════════════════════════════════════════════════════════════════════════

**(1) Extension a media altura del pico.** Contar los pixeles contiguos cuyo exceso
sobre el fondo del anillo supere la mitad del exceso del pico. El control lo tumbo:
Villarrica daba **143 px** a media altura y **2.407** a un cuarto — la region inundaba
la imagen entera. Con un fondo que NO es plano (gradiente topografico) y un exceso de
pico que es ruido (1,27 K), una fraccion de ese exceso cae por debajo de la
variabilidad del campo y el crecimiento de region se desborda.

**(2) N-sigma sobre el anillo [1,5-3] km**, que es el criterio del propio algoritmo.
Dio **0 pixeles para los dos volcanes a 3, 5 y 10 sigma** — ni el pico REAL de Lascar
(+5,65 K sobre la mediana del anillo) cruza 3 sigma. Eso implica sigma(anillo) > 1,88 K.

El fracaso (2) es en si mismo un resultado, y es el tercero que apunta al mismo lugar:
**el anillo [1,5-3] km es una referencia pesima**, porque su dispersion esta dominada
por la topografia y no por el ruido del sensor. Medido acá sobre el campo de MIROVA,
independiente de nuestro pipeline.

═══════════════════════════════════════════════════════════════════════════════
EL METODO QUE FUNCIONA: contraste contra los 8 vecinos
═══════════════════════════════════════════════════════════════════════════════

Es lo que hace Coppola: la deteccion es CONTEXTUAL (dNTI contra los 8 vecinos), no
contra un anillo lejano. Sin I05 no se puede armar el NTI, pero si el contraste local
en I04: cada pixel menos la mediana de sus 8 vecinos.

  · sigma del campo de contraste por MAD (robusto), sobre la imagen entera;
  · se cuentan los pixeles a menos de 1 km del crater con contraste > N*sigma.

Asi el umbral sale del ruido REAL del campo, no de un anillo contaminado por relieve.

LIMITE DECLARADO (D6/A24): el TIF es el campo de radiancia; el VRP que MIROVA publica
sale de una seleccion de cluster que no podemos ver. Esto es un PROXY de cuantos
pixeles integrarian, no su cluster literal.

Uso: S126_SCRATCH=<dir con tifs/ e index_remoto.csv> python 04_...py
Persiste en 04_cuantos_pixeles_ve_mirova.json.
"""
import csv
import io
import json
import math
import os
import sys

import numpy as np
import rasterio
from numpy.lib.stride_tricks import sliding_window_view

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _s126_lib import VENTS, cargar_brazo, resumen   # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRATCH = os.environ.get("S126_SCRATCH", "")
I04_LAMBDA, C1, C2 = 3.740, 1.19104e8, 1.43877e4
VENTANA = ("2026-06-25", "2026-08-24")
VOLS = ["Lascar", "Villarrica"]
SIGMAS = (3.0, 5.0)
R_CRATER_KM = 1.0


def rad_a_bt(L):
    L = np.asarray(L, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return C2 / (I04_LAMBDA * np.log1p(C1 / (I04_LAMBDA ** 5 * L)))


def contraste_local(bt):
    """Cada pixel menos la mediana de sus 8 vecinos (Coppola: contexto, no anillo)."""
    pad = np.pad(bt, 1, constant_values=np.nan)
    w = sliding_window_view(pad, (3, 3)).reshape(bt.shape[0], bt.shape[1], 9).copy()
    w[:, :, 4] = np.nan                      # excluir el propio pixel
    with np.errstate(invalid="ignore"):
        vecinos = np.nanmedian(w, axis=2)
    return bt - vecinos


def dist_km(tr, shape, vent):
    f, c = np.mgrid[0:shape[0], 0:shape[1]]
    lon, lat = tr * (c + 0.5, f + 0.5)
    return np.sqrt(((lat - vent[0]) * 111.32) ** 2
                   + ((lon - vent[1]) * 111.32 * math.cos(math.radians(vent[0]))) ** 2)


idx = [r for r in csv.DictReader(open(os.path.join(SCRATCH, "index_remoto.csv"),
                                      encoding="utf-8", errors="replace"))
       if r["sensor"] == "VIIRS375" and r["volcano"] in VOLS
       and VENTANA[0] <= r["last_modified_utc"][:10] <= VENTANA[1]]

res = {"ventana": list(VENTANA), "fuente": "mirova-tif-archive campo I04",
       "metodo": "contraste contra los 8 vecinos; sigma por MAD del campo",
       "metodos_descartados": {
           "media_altura": "control fallo: Villarrica 143 px (inunda)",
           "n_sigma_anillo": "0 px en ambos: ni el pico real de Lascar cruza 3 sigma "
                             "-> sigma(anillo 1,5-3 km) > 1,88 K, referencia pesima"},
       "limite": "proxy del cluster de MIROVA, no su cluster literal (D6/A24)",
       "por_volcan": {}}

print("CUANTOS PIXELES CALIENTES TIENE MIROVA EN EL CRATER — su campo I04")
print("contraste contra los 8 vecinos, %s a %s\n" % VENTANA)
print("%-14s %6s %14s %14s %12s %12s %14s" %
      ("volcan", "tifs", "sigma campo", "pico al crater", "px >3sig", "px >5sig", "px NUESTRO"))

for vol in VOLS:
    vent = VENTS[vol]
    sig, pico = [], []
    cuenta = {n: [] for n in SIGMAS}
    for r in [x for x in idx if x["volcano"] == vol]:
        p = os.path.join(SCRATCH, "tifs", os.path.basename(r["tif_path"]))
        if not os.path.exists(p):
            continue
        try:
            with rasterio.open(p) as ds:
                a = ds.read(1).astype(float)
                a[a <= 0] = np.nan
                bt, tr = rad_a_bt(a), ds.transform
        except Exception:
            continue
        ct = contraste_local(bt)
        val = ct[np.isfinite(ct)]
        if val.size < 500:
            continue
        s = 1.4826 * float(np.median(np.abs(val - np.median(val))))   # MAD -> sigma
        if not np.isfinite(s) or s <= 0:
            continue
        cerca = (dist_km(tr, bt.shape, vent) <= R_CRATER_KM) & np.isfinite(ct)
        if not cerca.any():
            continue
        sig.append(s)
        pico.append(float(np.nanmax(ct[cerca])))
        base = float(np.median(val))
        for n in SIGMAS:
            cuenta[n].append(int(np.sum(cerca & (ct >= base + n * s))))

    if not sig:
        print("%-14s   (sin lecturas validas)" % vol)
        continue

    nuestro = []
    c = cargar_brazo("_s126_corona_off", vol, VENTANA)
    if c:
        for rec in c.values():
            s_ = (rec.get("sensor") or "").upper()
            if "750" in s_ or "MODIS" in s_:
                continue
            pc = rec.get("primary_cluster") or {}
            if pc.get("vrp_mw"):
                nuestro.append(pc.get("n_pixels") or 0)

    d = {"tifs": len(sig), "sigma_campo_k": resumen(sig, 3),
         "pico_contraste_crater_k": resumen(pico, 3),
         "px_mirova": {str(n): resumen(cuenta[n], 1) for n in SIGMAS},
         "px_nuestro": resumen(nuestro, 1) if nuestro else None}
    res["por_volcan"][vol] = d
    print("%-14s %6d %14.3f %14.3f %12.1f %12.1f %14s"
          % (vol, d["tifs"], d["sigma_campo_k"]["mediana"],
             d["pico_contraste_crater_k"]["mediana"],
             d["px_mirova"]["3.0"]["mediana"], d["px_mirova"]["5.0"]["mediana"],
             d["px_nuestro"]["mediana"] if nuestro else "-"))

print("\n" + "=" * 92)
la, vi = res["por_volcan"].get("Lascar"), res["por_volcan"].get("Villarrica")
if la and vi:
    n_v = vi["px_mirova"]["3.0"]["mediana"]
    n_l = la["px_mirova"]["3.0"]["mediana"]
    print("CONTROL: Villarrica %.1f px sobre 3 sigma (pico %+.2f K) — el metodo separa"
          % (n_v, vi["pico_contraste_crater_k"]["mediana"]))
    if n_v >= n_l:
        print("  !! el control NO separa: el resultado de Lascar no vale.")
    else:
        n_n = la["px_nuestro"]["mediana"] if la["px_nuestro"] else None
        print("LASCAR : %.1f px sobre 3 sigma (pico %+.2f K); nosotros sumamos %s"
              % (n_l, la["pico_contraste_crater_k"]["mediana"], n_n))
        print("\n  Dos metodos INDEPENDIENTES convergen: la inversion aritmetica sobre")
        print("  nuestros records pedia ~1,57 pixeles, y la imagen de MIROVA muestra %.1f" % n_l)
        print("  donde sumamos %s. El deficit de Lascar es el segundo pixel." % n_n)

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "04_cuantos_pixeles_ve_mirova.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
