# -*- coding: utf-8 -*-
"""03c (S173): ¿la diferencia de VRP entre V0 (pipeline de hoy) y el port `fisica` del lote S162 en 6 pasadas es la
triangulación del fondo? Recalcula V0 con el fillmissing2 de la vía y con una interpolación lineal de scipy (Qhull,
la que usaba el port antes de la regla de empates de S163) sobre la MISMA grilla y la MISMA máscara.
P1: si la causa fuera otra, el VRP con Qhull no daría el del port. Uso: python -B 03c_fondo_qhull.py <raiz main>"""
import json, os, sys
from pathlib import Path
A = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1]).resolve(); sys.path[:0] = [str(RAIZ), str(A)]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np, yaml
from scipy.interpolate import griddata
import piezas as PZ
from pipeline import mirova_v750_codigo as MV
from pipeline.process_modis import merge_mir_bands
from pipeline.geo_utils import get_detection_anchor
RUN = Path(r"C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181")
obj = {o["id"]: o for o in json.load(open(A / "objetivos_neg_resto_modis.json", encoding="utf-8"))}
res = {}
for f in sorted(RUN.glob("s162-negmodis-MODIS-*/resultados_MODIS_*.json")):
    for r in json.load(open(f, encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
vols = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}


def fill_qhull(enm):
    n, m = enm.shape
    F, C = np.mgrid[0:n, 0:m]
    ok = np.isfinite(enm)
    out = enm.copy()
    out[~ok] = griddata(np.column_stack([F[ok], C[ok]]), enm[ok], (F[~ok], C[~ok]), method="linear")
    return out


L = []
for i in (65, 75, 97, 141, 1120, 1251):
    o, r = obj[i], res[i]
    n = np.load(next(RUN.glob(f"s162-negmodis-MODIS-*/nativo_{i:04d}.npz")))
    v = vols[o["volcan"]]
    g = MV.grilla_del_volcan(o["volcan"], paso_m=1000.0, clave_roi="roi_modis")
    rad = {"MIR": merge_mir_bands(n["b21"], n["b22"], True), "TIR": n["b31"]}
    m13, m15, box, pos = PZ.preparar_grilla(rad, n["lat_mxd03"].astype(float), n["lon_mxd03"].astype(float), g,
                                            get_detection_anchor(v), v.get("inner_radius_km"))
    mask = MV.detectar_mirova(m13, m15, box, int(r["dayflag"]), float(r["sunglint"]), lam_mir=PZ.LAM, lam_tir=PZ.FAM["lam_tir"])
    via = MV.vrp_mirova(m13, mask, coef=PZ.COEF)["VRP_MW"]
    orig = MV._fillmissing2_lineal
    try:
        MV._fillmissing2_lineal = fill_qhull
        qh = MV.vrp_mirova(m13, mask, coef=PZ.COEF)["VRP_MW"]
    finally:
        MV._fillmissing2_lineal = orig
    L.append(f"id {i} {o['volcan']} {o['hora_utc']}: VRP via {via:.4f} | con Qhull {qh:.4f} | port del lote "
             f"{r['port']['fisica']['vrp_mw']:.4f} | npix {int(mask.sum())} (port {r['port']['fisica']['npix']})")
print("\n".join(L)); (A / "03c_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
