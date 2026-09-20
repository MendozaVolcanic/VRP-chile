# -*- coding: utf-8 -*-
"""d05: audita scripts/libro_de_cuentas.py SIN ejecutarlo (escribe docs/LIBRO_DE_CUENTAS.json y corre pytest --co).
Replica sus tres funciones de datos (_ratios global, _ratios v375, recall_v750_dash) con su misma logica y ventana
(2026-01-01..2026-12-31) como CONTROL, y luego las parte por regimen (A104: #535 el 2026-08-28 23:00 UTC; #571 el 08-31)
y, para v375, cambia pc.vrp_mw por f5_core_vrp_mw (lo que el operador ve, A10 matiz S132).
Instrumento: (1) control = debe reproducir los declarados 0,73 / 0,69 / 85,06 dentro de la banda del libro; si el pareo
estuviera roto no lo haria. (2) n de pares impreso siempre: un 0 se ve."""
import io, sys, json, statistics as st
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
D = cargar()
def ratios(vent, buck=None, campo="pc"):
    mir, _ = cargar_mirova(vent); out = []
    for vol in VOLS:
        mejor = {}
        for r in D[vol]:
            if not es_noche(r): continue
            f = r["datetime_utc"][:10]
            if not (vent[0] <= f <= vent[1]): continue
            b = bucket(r.get("sensor")); v = pcv(r)
            if campo == "f5" and b == "v375" and r.get("f5_core_vrp_mw") is not None: v = r["f5_core_vrp_mw"] or 0
            if b is None or v <= 0 or (buck and b != buck): continue
            mejor[(f, b)] = max(mejor.get((f, b), 0), v)
        for k, v in mejor.items():
            m = (mir.get(vol) or {}).get(k)
            if m and m > 0: out.append(v/m)
    return (len(out), round(st.median(out), 3)) if out else (0, None)
def recall750(vent):
    mir, _ = cargar_mirova(vent); nuestras = set()
    for vol in VOLS:
        for r in D[vol]:
            if bucket(r.get("sensor")) != "v750": continue
            v = r.get("vrp_mw") or 0
            if not (v > 0 or r.get("triggered_test1") is True): continue
            if v == 0 and r.get("discarded_reason") and not r.get("triggered_test1"): continue
            dc = r.get("distance_class")
            if dc == "far": continue
            if dc != "summit" and not ((r.get("vrp_vent_mw") or 0) > 0): continue
            nuestras.add((vol, r["datetime_utc"][:10]))
    tot = ac = 0
    for vol in VOLS:
        for (d, b) in (mir.get(vol) or {}):
            if b == "v750": tot += 1; ac += ((vol, d) in nuestras)
    return (ac, tot, round(100*ac/tot, 2) if tot else None)
V = {"libro(2026 entero)": ("2026-01-01", "2026-12-31"), "previo(01-01..08-28)": ("2026-01-01", "2026-08-28"), "actual(09-01..09-19)": ("2026-09-01", "2026-09-19")}
out = {}
for n, w in V.items():
    out[n] = {"ratio_global_pc(n,mediana)": ratios(w), "ratio_v375_pc": ratios(w, "v375"), "ratio_v375_f5core": ratios(w, "v375", "f5"),
              "ratio_v750_pc": ratios(w, "v750"), "ratio_modis_pc": ratios(w, "modis"), "recall_v750_dash(ac,tot,pct)": recall750(w)}
json.dump(out, open("d05_libro_por_regimen.json", "w"), indent=1)
print(json.dumps(out, indent=1))
