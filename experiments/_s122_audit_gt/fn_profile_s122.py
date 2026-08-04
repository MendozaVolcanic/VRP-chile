#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EJE 6 S122 — perfil de los FN: MIROVA VRP de noches perdidas vs detectadas.
POR QUE: distingue FN sub-umbral (senal debil que no resolvemos) de FN de posicion/gate
(senal fuerte que perdimos = bug). Reusa la misma logica del audit principal."""
import json, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util
spec = importlib.util.spec_from_file_location("a", os.path.join(HERE, "audit_gt_s122.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)  # noqa

ROOT = sys.argv[1]
from collections import defaultdict
from pipeline.mirova_csv_loader import load_mirova_alertas
cons = os.path.join(ROOT, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
ocr = os.path.join(ROOT, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
START, END = "2026-01-10", "2026-07-20"
alertas = defaultdict(list)
for a in load_mirova_alertas(cons_path=cons, ocr_path=ocr):
    d = (a.get("fecha_utc") or "")[:10]
    if d and START <= d <= END:
        alertas[(a["volcano"], a["sensor_bucket"], d)].append(a["vrp_mw"])
ours = defaultdict(list)
for v in A.VOLS:
    dd = json.load(open(os.path.join(ROOT, "data/mirova_equivalent", v + ".json"), encoding="utf-8"))
    inner = A.INNER[v]
    for rec in dd["records"]:
        dt = rec.get("datetime_utc")
        b = A.our_bucket(rec.get("sensor", ""))
        if not dt or b is None: continue
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0; cd = pc.get("centroid_dist_km"); dc = rec.get("distance_class")
        if 0 < vrp <= A.CAP and cd is not None and cd <= inner and (not dc or dc == "summit"):
            ours[(v, b, dt[:10])].append(vrp)
res = {}
for s in A.SENSORS:
    fn, tp = [], []
    for (v, ss, d), vs in alertas.items():
        if ss != s: continue
        (tp if ours.get((v, ss, d)) else fn).append(max(vs))
    res[s] = dict(n_fn=len(fn), n_tp=len(tp),
                  fn_mirova_vrp_med=round(statistics.median(fn), 3) if fn else None,
                  tp_mirova_vrp_med=round(statistics.median(tp), 3) if tp else None,
                  fn_vrp_gt_1mw=sum(1 for x in fn if x > 1.0),
                  fn_vrp_gt_5mw=sum(1 for x in fn if x > 5.0))
    print(s, res[s])
json.dump(res, open(os.path.join(HERE, "fn_profile_s122.json"), "w"), indent=1)
