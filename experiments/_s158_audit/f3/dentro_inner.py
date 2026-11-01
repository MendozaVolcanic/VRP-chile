# -*- coding: utf-8 -*-
"""F3: comparación limpia de la misma región. Pares OSF 2025 clase 1, V375, en que TODOS los alertados de MIROVA están
dentro del inner_radius_km (Max_Dist <= inner): nuestra energía y conteo de alertados dentro del inner contra MIROVA,
por tramo fino de cenit. Quita el efecto de los alertados lejanos (que MIROVA no tiene en esas pasadas y nosotros sí).
Instrumento: (1) si nuestros píxeles no trajeran dist_km, n_in = 0 en todas y se vería; (2) la columna pub/M permite ver
cuánto de lo que queda es selección (núcleo F5' contra la suma dentro del inner).
Uso: python -B dentro_inner.py <raiz> pares_osf2025.csv
"""
import json, os, sys
import numpy as np, pandas as pd, yaml
ROOT, PARES = sys.argv[1], sys.argv[2]
KA = 18.0 * 140625
inner = {v["name"]: v.get("inner_radius_km", 10) for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
P = pd.read_csv(PARES, parse_dates=["t"])
P = P[(P.pareo == "ok") & (P.cls == 1) & (P.b == "V375")].copy()
P = P[P.maxd_M / 1000 <= P.vol.map(inner)]
recs = {}
for v in P.vol.unique():
    for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{v}.json"), encoding="utf-8"))["records"]:
        s = str(r.get("sensor")).upper()
        if "VIIRS" in s and "750" not in s:
            recs[(v, str(r["datetime_utc"])[:16])] = r
out = []
for _, m in P.iterrows():
    r = None
    for dm in range(6):
        for sg in (1, -1):
            r = recs.get((m.vol, (m.t + pd.Timedelta(minutes=sg * dm)).strftime("%Y-%m-%d %H:%M")))
            if r: break
        if r: break
    if not r:
        continue
    px = r.get("anomaly_pixels") or []
    if len(px) != (r.get("n_anomalous_pixels") or 0):
        continue
    inn = [p for p in px if p.get("dist_km") is not None and p["dist_km"] <= inner[m.vol]]
    pc = r.get("primary_cluster") or {}
    ok = r.get("distance_class") == "summit" and pc and (pc.get("centroid_dist_km") or 0) <= inner[m.vol]
    f5 = r.get("f5_core_vrp_mw")
    pub = ((f5 if isinstance(f5, (int, float)) and f5 > 0 else pc.get("vrp_mw") or 0) if ok else 0)
    out.append({"vol": m.vol, "zen": m.zen_M, "N_M": m.N_M, "M": m.VRP_M, "n_in": len(inn),
                "E_in": sum(p["vrp_mw"] for p in inn), "pub": pub})
D = pd.DataFrame(out)
D["tr"] = pd.cut(D.zen, [0, 10, 20, 30, 40, 50, 60, 75])
print(f"pares clase 1 V375 con todo MIROVA dentro del inner: {len(P)}; con record completo: {len(D)}; con n_in = 0: {int((D.n_in == 0).sum())}")
print("volcanes:", D.vol.value_counts().to_dict())
print("tramo | n | sum n_in/sum N_M | sum E_in/sum M | sum pub/sum M | mediana E_in/M")
for tr, g in D.groupby("tr", observed=True):
    if len(g) >= 8:
        print(f"{str(tr):9s} | {len(g):4d} | {g.n_in.sum() / g.N_M.sum():.3f} | {g.E_in.sum() / g.M.sum():.3f} | {g.pub.sum() / g.M.sum():.3f} | {(g.E_in / g.M).median():.3f}")
print("\npor volcán, cenit <= 30:")
g0 = D[D.zen <= 30]
print(g0.groupby("vol").apply(lambda g: pd.Series({"n": len(g), "n_in/N_M": g.n_in.sum() / g.N_M.sum(), "E_in/M": g.E_in.sum() / g.M.sum(), "pub/M": g.pub.sum() / g.M.sum()})).round(3).to_string())
