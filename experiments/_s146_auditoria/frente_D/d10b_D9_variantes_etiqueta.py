# -*- coding: utf-8 -*-
"""d10b: el '207 de 214 = 96,7 % MIROVA-confirmados ese sensor+noche' del cierre S113 de la divergencia D9 no se reproduce con pareo
(fecha, sensor) (d10: 12 %). Barre las definiciones de 'confirmado' y de 'path-D dominante' que S113 pudo usar, sobre 05-01..06-18,
records summit frios (t_bg<262) con pc.vrp>0. Tambien por volcan.
Instrumento: (1) si ninguna variante se acerca a 96,7 %, el numero es NO REPRODUCIBLE desde data de hoy (pudo cambiar por reproceso:
se declara). (2) el nulo: la misma tasa de confirmacion en summit NO frios, para saber cuanto vale."""
import io, sys, json
from collections import Counter, defaultdict
from datetime import date, timedelta
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
W = ("2026-05-01", "2026-06-18"); mir, _ = cargar_mirova(("2026-04-25", "2026-06-25")); D = cargar()
def pm1(f):
    y, m, d = map(int, f.split("-")); x = date(y, m, d); return {str(x + timedelta(days=k)) for k in (-1, 0, 1)}
PD = {"ctx>resto": lambda r: (r.get("diag_n_dnti_ctx_path") or 0) > (r.get("diag_n_bt_path") or 0) + (r.get("diag_n_nti_path") or 0) + (r.get("diag_n_eti_path") or 0),
      "ctx>0 y bt==0": lambda r: (r.get("diag_n_dnti_ctx_path") or 0) > 0 and (r.get("diag_n_bt_path") or 0) == 0,
      "ctx>0": lambda r: (r.get("diag_n_dnti_ctx_path") or 0) > 0}
out = {}
for nom, fpd in PD.items():
    for frio in (True, False):
        c = Counter(); pv = defaultdict(Counter)
        for v in VOLS:
            ks = set(mir.get(v) or {}); fechas = {d for d, b in ks}
            for r in D[v]:
                f = r["datetime_utc"][:10]
                if not (W[0] <= f <= W[1]) or r.get("distance_class") != "summit" or pcv(r) <= 0 or r.get("t_bg_k") is None: continue
                if (r["t_bg_k"] < 262) != frio or not fpd(r): continue
                b = bucket(r["sensor"]); c["n"] += 1; pv[v]["n"] += 1
                a = (f, b) in ks; bb = f in fechas; cc = any((g, b) in ks for g in pm1(f)); dd = any(g in fechas for g in pm1(f))
                c["mismo_sensor_misma_fecha"] += a; c["cualquier_sensor_misma_fecha"] += bb; c["mismo_sensor_pm1dia"] += cc; c["cualquier_sensor_pm1dia"] += dd
                pv[v]["conf_cualquier_pm1"] += dd
        out[f"{nom}|{'frio<262' if frio else 'NO frio (nulo)'}"] = {k: (v if k == "n" else (v, round(100*v/c["n"], 1))) for k, v in c.items()}
        if frio and nom == "ctx>resto": out["por_volcan(ctx>resto,frio)"] = {v: dict(x) for v, x in pv.items()}
json.dump(out, open("d10b_D9_variantes_etiqueta.json", "w"), indent=1); print(json.dumps(out, indent=1))
