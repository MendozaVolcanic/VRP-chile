#!/usr/bin/env python
"""201, efecto en lo publicado de VIIRS 375: cuantos records publicados tienen en su nucleo F5 (lo que
el tablero suma) algun pixel a mas de inner_radius_km del crater (zona donde rige el C1 de escena).
Pregunta 1: si el C1 de escena tocara la magnitud publicada, esos pixeles apareceran aqui. Pregunta 2:
control positivo con inner/4 (debe subir). Ventana 2026-03-01..2026-10-21, records nocturnos publicados.
"""
import json, os, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP / "scripts")); sys.path.insert(0, str(SNAP))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp, yaml
from pipeline.f5_core import _hav_km, F5_R_CORE_KM, F5_BT_EXT_K
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
vy = {v["name"]: v for v in yaml.safe_load(open(SNAP/"volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
recs = bp.cargar_nuestros(coords, inner, ("2026-03-01", "2026-10-21"))
pub = {(r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")) for r in recs if r["pub"]}
c = Counter(); L = []
for v in bp.VOLS:
    vv = vy[v]; vl, vo = vv["vent_lat"], vv["vent_lon"]
    for r in json.load(open(SNAP/"data"/"mirova_equivalent"/f"{v}.json", encoding="utf-8"))["records"]:
        if (v, r.get("sensor"), r.get("datetime_utc")) not in pub or bp.bucket(r.get("sensor")) != "VIIRS375":
            continue
        pc = r.get("primary_cluster") or {}; px = r.get("anomaly_pixels") or []
        c["pub_v375"] += 1
        if pc.get("centroid_lat") is None: continue
        cand = [p for p in px if p.get("lat") is not None and _hav_km(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= inner[v]]
        if not cand: continue
        pk = max(range(len(cand)), key=lambda i: cand[i].get("vrp_mw") or 0)
        keep = [p for i, p in enumerate(cand) if i == pk or _hav_km(p["lat"], p["lon"], cand[pk]["lat"], cand[pk]["lon"]) <= F5_R_CORE_KM or (p.get("bt_k") or 0) >= F5_BT_EXT_K]
        for fac, nom in [(1.0, "fuera_inner"), (0.25, "CONTROL_fuera_inner/4")]:
            fuera = [p for p in keep if _hav_km(vl, vo, p["lat"], p["lon"]) > inner[v]*fac]
            if fuera:
                c[nom] += 1
                if nom == "fuera_inner":
                    tot = sum(p.get("vrp_mw") or 0 for p in keep); f = sum(p.get("vrp_mw") or 0 for p in fuera)
                    c["mw_total"] += tot; c["mw_fuera"] += f
                    L.append(f"{v} {r['datetime_utc']} {r['sensor']} nucleo={len(keep)} fuera={len(fuera)} frac_mw={f/tot if tot else 0:.2f}")
print(dict(c)); print("\n".join(L[:15]))
Path(__file__).with_name("v_201_efecto_v375_salida.txt").write_text(json.dumps(dict(c)) + "\n" + "\n".join(L) + "\n", encoding="utf-8")
