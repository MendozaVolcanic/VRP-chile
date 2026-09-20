# Control H con filtro de usabilidad, control G deduplicado, filtro de region de S6 sobre la
# pasada de Lascar de M1. Solo lectura.
import os, sys, json, pickle, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
from cruz5 import df, idx_v  # noqa
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
import banco_paridad as bp
inner = bp.inner_desde_html()

print("== control H con TIF USABLE (v5 dice 128, 58 de Cordon Caulle) ==")
pos = df[(df.lab == "pos") & df.tif.notna()].copy()
usab = {}
for _, r in pos.iterrows():
    Rq, why = usable({"own": r["own"], "path": r["tif"]}, r["vol"])
    usab[(r["vol"], pd.Timestamp(r["dt"]).strftime("%Y-%m-%d %H:%M"))] = Rq is not None
    raster.cache_clear()
c1, c2 = {}, {}
for vol in VOLS:
    d = json.load(open(ROOT + f"/data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        k = (vol, (r.get("datetime_utc") or "")[:16])
        if not usab.get(k):
            continue
        pc = r.get("primary_cluster") or {}
        n = pc.get("n_pixels") or 0
        la, lo = pc.get("centroid_lat"), pc.get("centroid_lon")
        if n >= 2 and la is not None and hav(la, lo, *vent(vol)) <= inner[vol]:
            c1[vol] = c1.get(vol, 0) + 1
            if r.get("final_hotspot_source") == "ctx_cluster":
                c2[vol] = c2.get(vol, 0) + 1
print("  primary_cluster>=2px dentro del inner, TIF usable: %d  %s" % (sum(c1.values()), c1))
print("  + final_hotspot_source=='ctx_cluster':            %d  %s" % (sum(c2.values()), c2))

print("\n== control G deduplicado por pasada (v5: '42 de 43 pasadas' son de Lascar) ==")
d = ref()
tot = {}
for vol in ("Lascar", "Villarrica"):
    s = d[(d.vol == vol) & (d.src == "CONS") & (pd.to_numeric(d.VRP_MW, errors="coerce") >= 0.3)]
    s = s[s.t >= pd.Timestamp("2026-05-09", tz="UTC")]
    vistos, n = set(), 0
    for _, r in s.iterrows():
        g = idx_v.get(vol)
        dd = (g.acquisition_utc - r["t"]).dt.total_seconds().abs()
        if not (dd <= 120).any():
            continue
        rr = g.loc[dd.idxmin()]
        k = (vol, rr["acquisition_utc"])
        if k in vistos:
            continue
        Rq, why = usable({"own": bool(rr["own"]), "path": rr["path"]}, vol)
        if Rq is None:
            continue
        vistos.add(k); n += 1
    raster.cache_clear()
    tot[vol] = n
    print("   %-12s filas CONS VRP>=0,3: %3d   pasadas distintas con TIF usable: %3d" % (vol, len(s), n))
print("   total del pool G: %d   fraccion Lascar: %.2f" % (sum(tot.values()), tot["Lascar"] / max(1, sum(tot.values()))))

print("\n== filtro de region de S6 sobre la pasada de Lascar de M1 ==")
pool = pickle.load(open(V3 + "/pool3.pkl", "rb"))["df"]
cons = d[(d.src == "CONS") & d.Tipo_Registro.astype(str).str.startswith("ALERTA")]
sub = pool[(pool.lab == "pos") & pool.patron & pool.tif.notna() & (pool.dPF >= 1.5) & (pool.vol == "Lascar")]
for _, r in sub.iterrows():
    g = cons[cons.vol == "Lascar"]
    dd = (g.t - pd.Timestamp(r["dt"])).dt.total_seconds().abs()
    if not (dd <= 120).any():
        continue
    f = g.loc[dd.idxmin()]
    D = float(f["Distancia_km"])
    v = vent("Lascar"); c = mc("Lascar")
    for nom, pt in (("P", r["P"]), ("F", r["F"])):
        d_v = hav(pt[0], pt[1], v[0], v[1]); d_c = hav(pt[0], pt[1], c[0], c[1])
        print("   %s: d(crater)=%.2f km (disco 3,4) ; d(mirova_center)=%.2f km (disco D+1=%.2f) -> dentro=%s"
              % (nom, d_v, d_c, D + 1, (d_v <= 3.4) or (d_c <= D + 1)))
    print("   dt=%s  D=%.2f  d(P,F)=%.2f  |rP_mc - D|=%.2f" %
          (r["dt"], D, r["dPF"], abs(hav(r["P"][0], r["P"][1], c[0], c[1]) - D)))
