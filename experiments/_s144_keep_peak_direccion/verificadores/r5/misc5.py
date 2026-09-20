# Comprobaciones sueltas de la v5: geometria de los sitios de referencia, S1, S2, control H,
# control G (conteo), M1 (conteo del universo). Solo lectura.
import os, sys, json, pickle, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
from cruz5 import df, idx_v, zc, refs_de, POOL, MINGAP_S  # noqa
import base4 as B  # noqa

geomP = B.geomP
print("== S1: geometria de P (v5 dice radio mediano 2,79 km, maximo 3,00) ==")
print("  n=%d  mediana=%.3f  p99=%.2f  max=%.3f  frac en [1,5-3,0]=%.4f"
      % (len(geomP), geomP.rP.median(), geomP.rP.quantile(.99), geomP.rP.max(),
         float(((geomP.rP >= 1.5) & (geomP.rP <= 3.0)).mean())))

M2 = df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].copy()
print("\n== S1: persistencia (v5 dice 97,1 %% con otro P a <=0,75 km en otra noche, mediana 12) ==")
fil = []
for v, g in M2.groupby("vol"):
    la = np.array([p[0] for p in g.P]); lo = np.array([p[1] for p in g.P]); nn = g.noche.values
    for i in range(len(g)):
        d = hav(la, lo, la[i], lo[i])
        fil.append(len(set(nn[d <= 0.75]) - {nn[i]}))
fil = np.array(fil)
print("  n=%d  frac>=1: %.4f  mediana de otras noches: %.0f" % (len(fil), (fil >= 1).mean(), np.median(fil)))

print("\n== geometria de los 5 sitios de referencia (muestra del veredicto) ==")
rows = []
for vol, g in M2.groupby("vol"):
    v = vent(vol)
    for _, r in g.iterrows():
        R = refs_de(vol, r["t"], r["noche"], r["P"])
        if len(R) < 3:
            continue
        pts = [p for p, _ in R]
        la = np.array([p[0] for p in pts]); lo = np.array([p[1] for p in pts])
        # cuantos sitios DISTINTOS (aglomerado simple a 0,75 km)
        usados, grupos = set(), 0
        for i in range(len(pts)):
            if i in usados:
                continue
            grupos += 1
            for j in range(len(pts)):
                if hav(la[j], lo[j], la[i], lo[i]) <= 0.75:
                    usados.add(j)
        dref = hav(la, lo, r["P"][0], r["P"][1])
        # acimut relativo al crater
        def az(p):
            dn = (p[0] - v[0]) * 110.574
            de = (p[1] - v[1]) * 111.320 * math.cos(math.radians(v[0]))
            return math.degrees(math.atan2(de, dn)) % 360
        aP = az(r["P"])
        da = [min(abs(az(p) - aP), 360 - abs(az(p) - aP)) for p in pts]
        rows.append(dict(vol=vol, n_sitios=grupos, d_min=float(dref.min()), d_med=float(np.median(dref)),
                         da_med=float(np.median(da)), rP=hav(r["P"][0], r["P"][1], v[0], v[1])))
G = pd.DataFrame(rows)
print("  sitios distintos entre las 5 referencias (aglomerado a 0,75 km):",
      G.n_sitios.value_counts().sort_index().to_dict())
print("  distancia de las referencias a P: mediana %.2f km (min de las 5: mediana %.2f km)"
      % (G.d_med.median(), G.d_min.median()))
print("  diferencia de acimut respecto del crater: mediana %.0f grados  p10 %.0f  p90 %.0f"
      % (G.da_med.median(), G.da_med.quantile(.1), G.da_med.quantile(.9)))
print("  por volcan (sitios distintos medianos):", G.groupby("vol").n_sitios.median().to_dict())

print("\n== control H (v5 dice 128 pasadas, 58 de Cordon Caulle) ==")
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
import banco_paridad as bp
inner = bp.inner_desde_html()
pos = df[(df.lab == "pos") & df.tif.notna()].copy()
key = {(r.vol, pd.Timestamp(r.dt).strftime("%Y-%m-%d %H:%M")) for r in pos.itertuples()}
c1, c2 = {}, {}
for vol in VOLS:
    d = json.load(open(ROOT + f"/data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        if (vol, (r.get("datetime_utc") or "")[:16]) not in key:
            continue
        pc = r.get("primary_cluster") or {}
        n = pc.get("n_pixels") or 0
        la, lo = pc.get("centroid_lat"), pc.get("centroid_lon")
        if n >= 2 and la is not None and hav(la, lo, *vent(vol)) <= inner[vol]:
            c1[vol] = c1.get(vol, 0) + 1
            if r.get("final_hotspot_source") == "ctx_cluster":
                c2[vol] = c2.get(vol, 0) + 1
print("  primary_cluster >=2 px dentro del inner: %d  %s" % (sum(c1.values()), c1))
print("  + final_hotspot_source=='ctx_cluster':   %d  %s" % (sum(c2.values()), c2))

print("\n== control G (v5 dice 'valida casi solo Lascar, 42 de 43 pasadas') ==")
d = ref()
for vol in ("Lascar", "Villarrica"):
    csvn = CSVN.get(vol, vol)
    s = d[(d.vol == vol) & (d.src == "CONS") & (d.VRP_MW >= 0.3)] if "VRP_MW" in d.columns else None
    cols = [c for c in d.columns if "vrp" in c.lower() or "VRP" in c]
    print("   columnas VRP del CSV:", cols[:6])
    break
col = [c for c in d.columns if c.lower().startswith("vrp")][0]
tipo = [c for c in d.columns if "tipo" in c.lower() or "Tipo" in c]
print("   col VRP:", col, " col tipo:", tipo)
for vol in ("Lascar", "Villarrica"):
    csvn = CSVN.get(vol, vol)
    s = d[(d.vol == vol) & (d.src == "CONS") & (pd.to_numeric(d[col], errors="coerce") >= 0.3)]
    s = s[(s.t >= pd.Timestamp("2026-05-09", tz="UTC"))]
    n_tif = 0
    for _, r in s.iterrows():
        g = idx_v.get(vol)
        if g is None:
            continue
        dd = (g.acquisition_utc - r["t"]).dt.total_seconds().abs()
        if (dd <= 120).any():
            rr = g.loc[dd.idxmin()]
            Rq, why = usable({"own": bool(rr["own"]), "path": rr["path"]}, vol)
            if Rq is not None:
                n_tif += 1
    print("   %-12s filas CONS con VRP>=0,3: %3d   con TIF usable: %3d" % (vol, len(s), n_tif))
