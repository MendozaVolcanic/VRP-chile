# Control G con la redaccion de la v3 (mediana por eje, semilla con z >= zc_punto).
import os, sys, math, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common3 import *  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
null = pd.read_pickle(HERE + "/null3.pkl")
ok = null[null.estado == "ok"]
zc = ok.groupby("vol").zu.quantile(0.95).to_dict()
print("zc_punto usado (del pool nulo):", {k: round(v, 2) for k, v in zc.items()})

idx = load_idx("VIIRS375")
idx_v = {v: g.sort_values("acquisition_utc") for v, g in idx.groupby("vol")}
d = ref()


def tif_de(vol, t, tol=120):
    g = idx_v.get(vol)
    if g is None:
        return None
    dd = (g.acquisition_utc - t).dt.total_seconds().abs()
    if not (dd <= tol).any():
        return None
    return g.loc[dd.idxmin()]


def semilla_disco(R, centro, r_km=4.0):
    dd = hav(R["lat"], R["lon"], centro[0], centro[1])
    m = (dd <= r_km) & np.isfinite(R["z"])
    if not m.any():
        return None
    zz = np.where(m, R["z"], -np.inf)
    i = np.unravel_index(np.argmax(zz), zz.shape)
    return dict(z=float(R["z"][i]), lat=float(R["lat"][i]), lon=float(R["lon"][i]))


rows = []
for vol in ["Lascar", "Villarrica"]:
    g = d[(d.vol == vol) & (d.src == "CONS") & d.Tipo_Registro.astype(str).str.startswith("ALERTA")]
    g = g[(g.VRP_MW.astype(float) >= 0.3)]
    for _, f in g.iterrows():
        t = f["t"]
        if not (3 <= t.hour <= 9):
            continue
        tt = tif_de(vol, t)
        if tt is None:
            continue
        R, why = usable({"own": tt["own"], "path": tt["path"]}, vol)
        if R is None:
            continue
        v = vent(vol)
        s = semilla_disco(R, v)
        if s is None:
            continue
        dn = (s["lat"] - v[0]) * 110.574
        de = (s["lon"] - v[1]) * 111.320 * math.cos(math.radians(v[0]))
        rows.append(dict(vol=vol, t=t, z=s["z"], dist=hav(s["lat"], s["lon"], *v), dn=dn, de=de,
                         pasa_z=s["z"] >= zc.get(vol, 0), celda=celda_km(R)))

G = pd.DataFrame(rows).drop_duplicates(subset=["vol", "t"])
print("\n== control G, v3 (n bruto=%d) ==" % len(G))
print(G.vol.value_counts().to_dict())
for etiqueta, sub in [("sin exigir z >= zc_punto", G), ("con z >= zc_punto", G[G.pasa_z])]:
    if not len(sub):
        continue
    print(f"\n  [{etiqueta}] n={len(sub)}  (Lascar {int((sub.vol=='Lascar').sum())}, Villarrica {int((sub.vol=='Villarrica').sum())})")
    print("   frac dist <= 0,75 km: %.3f   mediana dist: %.3f" % ((sub.dist <= 0.75).mean(), sub.dist.median()))
    print("   NS: mediana %+.3f  media %+.3f   EW: mediana %+.3f  media %+.3f"
          % (sub.dn.median(), sub.dn.mean(), sub.de.median(), sub.de.mean()))
    ok_g = (len(sub) >= 8 and (sub.dist <= 0.75).mean() >= 0.80 and sub.dist.median() <= 0.5
            and abs(sub.dn.median()) < 0.19 and abs(sub.de.median()) < 0.19)
    print("   -> G %s" % ("PASA" if ok_g else "FALLA"))
print("\n frac de pasadas con alerta cuya semilla cumple z >= zc_punto: %.3f" % G.pasa_z.mean())
print(" celda (km): ", G.celda.iloc[0] if len(G) else None)

# el gate de z aplicado a pasadas RUTINA: cuan exigente es
print("\n== cuan exigente es 'z de la semilla del disco de 4 km >= zc_punto' en pasadas RUTINA ==")
pool = pickle.load(open(HERE + "/pool3.pkl", "rb"))["df"]
rut = pool[(pool.lab == "neg_limpio") & (~(pool.patron & pool.pub)) & pool.tif.notna()]
res = []
for vol, gg in rut.groupby("vol"):
    gg = gg.head(40)
    cnt = 0; n = 0
    for _, r in gg.iterrows():
        R, why = usable({"own": r["own"], "path": r["tif"]}, vol)
        if R is None:
            continue
        s = semilla_disco(R, vent(vol))
        if s is None:
            continue
        n += 1; cnt += s["z"] >= zc.get(vol, 1e9)
    if n:
        res.append((vol, n, cnt / n))
for vol, n, f in res:
    print("  %-22s n=%3d  frac(max del disco de 4 km >= zc_punto) = %.3f" % (vol, n, f))
