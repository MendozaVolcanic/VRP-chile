# -*- coding: utf-8 -*-
"""S131 auditoria MAGNITUD - lo que VE el operador no es pc.vrp_mw en VIIRS375.

POR QUE. `frontend/index.html:1015` arranca con `USE_F5_CORE = true`: para VIIRS375 el
dashboard muestra `f5CoreMagnitude` (suma de los anomaly_pixels a <=0.75 km del pixel de
maxima energia dentro de inner_radius del centroide, o con bt>=295 K), no `pc.vrp_mw`.
Este script replica esa funcion en Python y compara AMBAS contra MIROVA con los mismos
pares por pasada del script 03 (|dt|<=20 min, nocturnas, 2026, 11 Tier A).
"""
import io, json, os, sys, csv, statistics as st, math
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "experiments")); sys.path.insert(0, HERE)
from _s126_lib import ALIAS, bucket, haversine, ic95
import importlib; m03 = importlib.import_module("03_pares_por_pasada")
INNER = {"Chaiten":5,"Copahue":4,"Isluga":5,"Lascar":5,"Lastarria":3,"Llaima":5,"NevadosDeChillan":5,
         "PlanchonPeteroa":3,"PuyehueCordonCaulle":20,"Tupungatito":7,"Villarrica":5}
R_CORE, BT_EXT, TOL = 0.75, 295.0, timedelta(minutes=20)

def f5(r, inner):
    px = r.get("anomaly_pixels") or []; pc = r.get("primary_cluster") or {}
    if not px or pc.get("centroid_lat") is None: return None
    c = (pc["centroid_lat"], pc["centroid_lon"])
    cand = [p for p in px if p.get("lat") is not None and haversine(c, (p["lat"], p["lon"])) <= inner]
    if not cand: return None
    peak = max(cand, key=lambda p: p.get("vrp_mw") or 0)
    s = 0.0
    for p in cand:
        if p is peak or haversine((peak["lat"], peak["lon"]), (p["lat"], p["lon"])) <= R_CORE or (p.get("bt_k") or 0) >= BT_EXT:
            s += p.get("vrp_mw") or 0
    return s

gt = m03.cargar_gt_por_pasada(("2026-01-01", "2026-12-31"))
rows = []
for v in ALIAS:
    for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        if bucket(r.get("sensor")) != "v375": continue
        sol = r.get("solar_zenith_deg")
        if sol is not None and sol < 90: continue
        pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        if pcv <= 0 or not ("2026-01-01" <= r["datetime_utc"][:10] <= "2026-12-31"): continue
        dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        cand = [(abs(g[0]-dt), g) for g in gt.get((v, "v375"), []) if abs(g[0]-dt) <= TOL]
        if not cand: continue
        gv = min(cand, key=lambda x: x[0])[1][1]
        core = f5(r, INNER[v]); disp = core if core is not None and core > 0 else pcv
        rows.append((v, pcv, disp, gv))
def med(x): return round(st.median(x), 3)
res = {"definicion": __doc__, "n": len(rows)}
rp = [a/c for _, a, b, c in rows]; rd = [b/c for _, a, b, c in rows]
res["global"] = {"pc_vrp_mw": {"mediana": med(rp), "ic95": ic95(rp)}, "display_f5": {"mediana": med(rd), "ic95": ic95(rd)},
                 "display_igual_a_pc_pct": round(100*sum(1 for _,a,b,_ in rows if abs(a-b) < 1e-6)/len(rows),1)}
print(f"VIIRS375 pares por pasada n={len(rows)}: ratio pc.vrp_mw mediana={med(rp)} IC95={ic95(rp)} | ratio DISPLAY F5' mediana={med(rd)} IC95={ic95(rd)} | display==pc en {res['global']['display_igual_a_pc_pct']}%")
res["por_volcan"] = {}
for v in ALIAS:
    xs = [t for t in rows if t[0] == v]
    if len(xs) < 15: res["por_volcan"][v] = {"n": len(xs)}; continue
    a = med([t[1]/t[3] for t in xs]); b = med([t[2]/t[3] for t in xs])
    res["por_volcan"][v] = {"n": len(xs), "pc": a, "display_f5": b}
    print(f"  {v:20s} n={len(xs):4d} pc={a:.3f} display_f5={b:.3f}")
json.dump(res, open(os.path.join(HERE, "04_display_f5_vs_pc.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
