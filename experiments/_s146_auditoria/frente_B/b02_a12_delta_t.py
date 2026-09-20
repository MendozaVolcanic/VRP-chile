# -*- coding: utf-8 -*-
"""S146 B: A12 dT (libro_de_cuentas r_delta_t) bajo tres denominadores.
1. Si lo medido estuviera roto (dT no dependiera del denominador) las tres columnas darian igual: se veria.
2. Instrumento muerto -> n=0 impreso, no un numero. Read-only."""
import json, os, statistics as st, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for vol in ("Lascar", "Isluga"):
    recs = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]
    def dts(f):
        out = []
        for r in recs:
            s = r.get("sensor") or ""
            if not s.startswith("VIIRS") or s.endswith("_750"): continue
            tm = r.get("t_max_i04_k") or r.get("t_max_k"); tb = r.get("t_bg_k")
            if tm is None or tb is None or not f(r): continue
            out.append(tm - tb)
        return out
    todos = dts(lambda r: True)
    det = dts(lambda r: ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0 and r.get("distance_class") == "summit")
    nodet = dts(lambda r: not (((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0))
    for n, x in (("todos los records V375", todos), ("solo detecciones summit con pc.vrp>0", det), ("sin deteccion", nodet)):
        print(f"{vol:8s} {n:40s} n={len(x):5d} mediana dT={st.median(x):6.1f} K" if x else f"{vol} {n} n=0")
