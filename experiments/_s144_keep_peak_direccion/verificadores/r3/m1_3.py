# M1: geometria del anillo, zc_anillo y fuente persistente. Sin clasificar ninguna pasada.
import os, sys, math, pickle, collections
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common3 import *  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
pool = pickle.load(open(HERE + "/pool3.pkl", "rb"))["df"]
d = ref()

print("== separacion mirova_center - crater (km) ==")
for v in VOLS:
    print("  %-22s %.2f" % (v, hav(*mc(v), *vent(v))))

# --- universo de M1: pasadas con alerta CONS, patron, no 'cerca', con TIF usable
idx = load_idx("VIIRS375")
idx_v = {v: g.sort_values("acquisition_utc") for v, g in idx.groupby("vol")}


def tif_de(vol, t, tol=120):
    g = idx_v.get(vol)
    if g is None:
        return None
    dd = (g.acquisition_utc - pd.Timestamp(t)).dt.total_seconds().abs()
    if not (dd <= tol).any():
        return None
    return g.loc[dd.idxmin()]


cons = d[(d.src == "CONS") & d.Tipo_Registro.astype(str).str.startswith("ALERTA")]
filas = []
sub = pool[(pool.lab == "pos") & pool.patron & pool.tif.notna() & (pool.dPF >= 1.5)]
for _, r in sub.iterrows():
    g = cons[(cons.vol == r["vol"])]
    dd = (g.t - pd.Timestamp(r["dt"])).dt.total_seconds().abs()
    if not len(g) or not (dd <= 120).any():
        continue
    f = g.loc[dd.idxmin()]
    R, why = usable({"own": r["own"], "path": r["tif"]}, r["vol"])
    if R is None:
        continue
    rP_mc = hav(r["P"][0], r["P"][1], *mc(r["vol"]))
    filas.append(dict(vol=r["vol"], dt=r["dt"], D=float(f["Distancia_km"]), rP_mc=rP_mc,
                      compat=abs(rP_mc - float(f["Distancia_km"])) <= 0.55,
                      rP_vent=r["rP"], dPF=r["dPF"]))
M = pd.DataFrame(filas)
print("\n== universo M1 (alerta CONS, patron, no 'cerca' (d(P,F)>=1,5), TIF usable) ==")
print("total:", len(M))
for v, g in M.groupby("vol"):
    print("  %-22s n=%2d  compatibles (|rP_mc - D| <= 0,55): %d   D: %s" %
          (v, len(g), int(g.compat.sum()), sorted(set(round(x, 2) for x in g.D))[:8]))
print("\nfuera de Lastarria: n=%d compatibles=%d ; Lastarria: n=%d compatibles=%d"
      % ((M.vol != "Lastarria").sum(), int(M[M.vol != "Lastarria"].compat.sum()),
         (M.vol == "Lastarria").sum(), int(M[M.vol == "Lastarria"].compat.sum())))

# --- alcanzabilidad geometrica de la clase F: hace falta |D - sep| <= 0,6 + 0,75
print("\n== clase F alcanzable? (el anillo |r-D|<=0,6 en torno a mirova_center pasa a <=0,75 km del crater) ==")
M["sep"] = M.vol.map(lambda v: hav(*mc(v), *vent(v)))
M["F_alcanzable"] = (M.D - M.sep).abs() <= 0.6 + 0.75
comp = M[M.compat]
print("  sobre las compatibles (n=%d): F alcanzable en %d" % (len(comp), int(comp.F_alcanzable.sum())))
for v, g in comp.groupby("vol"):
    print("    %-22s n=%2d  F alcanzable=%d" % (v, len(g), int(g.F_alcanzable.sum())))

# --- zc_anillo y fuente persistente en Lastarria
print("\n== zc_anillo y anillo en pasadas RUTINA de Lastarria ==")
rut = pool[(pool.lab == "neg_limpio") & (pool.vol == "Lastarria") & pool.tif.notna()]
Ds = sorted(set(round(x, 2) for x in comp[comp.vol == "Lastarria"].D)) or [1.19, 1.55, 2.40]
print("  D que aparecen en M1 (Lastarria):", Ds)
cache = []
for _, r in rut.iterrows():
    R, why = usable({"own": r["own"], "path": r["tif"]}, "Lastarria")
    if R is not None:
        cache.append(R)
print("  pasadas RUTINA con TIF usable:", len(cache))
c = mc("Lastarria"); v = vent("Lastarria")
for D in Ds:
    maxs, locs, ncel = [], [], []
    for R in cache:
        rr = hav(R["lat"], R["lon"], c[0], c[1])
        m = (np.abs(rr - D) <= 0.6) & np.isfinite(R["z"])
        ncel.append(int(m.sum()))
        if not m.any():
            continue
        zz = np.where(m, R["z"], -np.inf)
        i = np.unravel_index(np.argmax(zz), zz.shape)
        maxs.append(float(R["z"][i]))
        locs.append(round(float(hav(R["lat"][i], R["lon"][i], v[0], v[1])), 3))
    if maxs:
        print("   D=%.2f  celdas del anillo: %d-%d  zc_anillo(p95)=%.2f  mediana del max=%.2f"
              % (D, min(ncel), max(ncel), float(np.percentile(maxs, 95)), float(np.median(maxs))))
        cnt = collections.Counter(locs).most_common(4)
        print("        distancia al crater del maximo del anillo en RUTINA (top): %s  (n=%d)" % (cnt, len(locs)))
