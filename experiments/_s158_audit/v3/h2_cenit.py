# -*- coding: utf-8 -*-
"""V3, F3-H2: ¿la pendiente de la magnitud V375 con el cenit es de conteo (Npix nuestro cae, el de MIROVA no)?
Población: pares OSF v2.5 2025 clase 1, V375, noche, |dt|<=5 min (pares_osf2025_v3.csv, re-generado por mí con el
script de F3 y comparado celda a celda con el suyo: idéntico), con todos los alertados de MIROVA a <= inner (Max_Dist)
y lista de píxeles completa (n_anomalous_pixels <= 100).
Diferencias contra F3: (1) la distancia de cada píxel nuestro se mide DESDE EL CRÁTER (ancla del pipeline,
get_detection_anchor), no desde dist_km del record (que mide desde el centro del volcán; PCC 7,6 km, Tupungatito 2,7);
(2) estratifico por volcán (Simpson) y doy razones ponderadas por volcán.
P1: si la pendiente no fuera de conteo, n_in/N_M sería plana y el exceso por píxel caería; se imprimen las dos.
P2: pares con n_in = 0 se cuentan aparte. Control positivo: N_M de MIROVA por tramo (debe crecer si MIROVA no
remuestreara; plano si sí) y el cenit nuestro igual al de MIROVA (pareo).
"""
import sys, io, json, os
from pathlib import Path
import numpy as np, pandas as pd, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.geo_utils import get_detection_anchor
Y = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def hav(a, b, c, d):
    p1, p2 = np.radians(a), np.radians(c); dp = p2 - p1; dl = np.radians(d - b)
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2))
P = pd.read_csv(Path(__file__).with_name("pares_osf2025_v3.csv"), parse_dates=["t"])
P = P[(P.pareo == "ok") & (P.cls == 1) & (P.b == "V375")].copy()
P["inner"] = P.vol.map(lambda v: Y[v]["inner_radius_km"])
P = P[P.maxd_M / 1000 <= P.inner]
recs = {}
for v in P.vol.unique():
    lst = []
    for r in json.load(open(ROOT / "data" / "mirova_equivalent" / f"{v}.json", encoding="utf-8"))["records"]:
        s = str(r.get("sensor")).upper()
        if s.startswith("VIIRS") and not s.endswith("_750") and str(r["datetime_utc"]).startswith("2025"):
            lst.append((pd.Timestamp(r["datetime_utc"]), r))
    recs[v] = lst
out = []
for _, m in P.iterrows():
    t0, r = min(recs[m.vol], key=lambda x: abs(x[0] - m.t))
    if abs((t0 - m.t).total_seconds()) > 300:
        continue
    px = r.get("anomaly_pixels") or []
    if len(px) != (r.get("n_anomalous_pixels") or 0):
        continue
    alat, alon = get_detection_anchor(Y[m.vol])
    dv = np.array([hav(alat, alon, p["lat"], p["lon"]) for p in px]) if px else np.array([])
    dc = np.array([p["dist_km"] for p in px]) if px else np.array([])
    e = np.array([p["vrp_mw"] for p in px]) if px else np.array([])
    out.append({"vol": m.vol, "zen": m.zen_M, "N_M": m.N_M, "M": m.VRP_M,
                "n_v": int((dv <= m.inner).sum()), "E_v": float(e[dv <= m.inner].sum()) if len(e) else 0.0,
                "n_c": int((dc <= m.inner).sum()), "E_c": float(e[dc <= m.inner].sum()) if len(e) else 0.0})
D = pd.DataFrame(out)
D["tr"] = pd.cut(D.zen, [0, 10, 20, 30, 40, 50, 60, 75])
print(f"pares: {len(D)}; n_v=0: {(D.n_v==0).sum()}; n_c=0: {(D.n_c==0).sum()}; pares donde n_v != n_c: {(D.n_v!=D.n_c).sum()}")
print("\nAGREGADO (sumas): tramo | n | N_M medio | n_v medio | Σn_v/ΣN_M | ΣE_v/ΣM | ΣE_c/ΣM (F3) | exceso por píxel (E_v/n_v)/(M/N_M)")
for tr, g in D.groupby("tr", observed=True):
    gg = g[g.n_v > 0]
    epp = (gg.E_v.sum() / gg.n_v.sum()) / (gg.M.sum() / gg.N_M.sum())
    print(f"{str(tr):9s} | {len(g):4d} | {g.N_M.mean():6.2f} | {g.n_v.mean():6.2f} | {g.n_v.sum()/g.N_M.sum():.3f} | {g.E_v.sum()/g.M.sum():.3f} | {g.E_c.sum()/g.M.sum():.3f} | {epp:.3f}")
print("\nPOR VOLCÁN (>=40 pares): razón de sumas E_v/M y n_v/N_M, cenit <=20 / 20-40 / >40; N_M medio en los mismos tramos")
D["t3"] = pd.cut(D.zen, [0, 20, 40, 75], labels=["<=20", "20-40", ">40"])
for v, g in D.groupby("vol"):
    if len(g) < 40:
        continue
    row = []
    for t3, h in g.groupby("t3", observed=True):
        row.append(f"{t3}: n={len(h):3d} E={h.E_v.sum()/h.M.sum():.2f} N={h.n_v.sum()/h.N_M.sum():.2f} NM={h.N_M.mean():.1f}")
    from scipy.stats import spearmanr
    rho = spearmanr(g.zen, g.E_v / g.M).correlation
    rhoN = spearmanr(g.zen, g.N_M).correlation
    print(f"{v:20s} " + " | ".join(row) + f" | rho(zen,E/M)={rho:+.2f} rho(zen,N_M)={rhoN:+.2f}")
# razón ponderada por volcán (cada volcán pesa igual) por tramo t3
print("\nRAZÓN E_v/M promediando volcanes (cada volcán con >=8 pares en el tramo pesa igual):")
for t3, h in D.groupby("t3", observed=True):
    vals = [g.E_v.sum() / g.M.sum() for _, g in h.groupby("vol") if len(g) >= 8]
    print(f"  {t3}: {np.mean(vals):.3f} sobre {len(vals)} volcanes")
