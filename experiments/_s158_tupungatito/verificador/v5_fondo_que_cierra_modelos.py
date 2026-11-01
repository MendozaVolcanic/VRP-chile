# -*- coding: utf-8 -*-
"""Verificador S158. ¿La planitud del «fondo que cierra con área» (5,0 / 4,2 / 5,5 K) es propiedad de los datos o
del modelo de área? Recalcula, con los mismos píxeles K y la misma bisección de e_fondo_local.py, el fondo que
cierra M / f para cuatro leyes de área: sin área (f = 1), f_modelo (brazo B de S131), f_lineal (brazo C de S131)
y raíz de f_modelo (la mitad del efecto en log). Si varias leyes muy distintas dan «plano», la planitud no
discrimina; si sólo la del modelo B lo da, el resultado es específico.

Uso: python -I v5_fondo_que_cierra_modelos.py
"""
import io
import json
import math
import os
import statistics as st
import sys
from importlib import import_module
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "_s131_audit" / "magnitud"))
sys.path.insert(0, str(ROOT / "experiments"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK  # noqa: E402
from pipeline import process_viirs as pv  # noqa: E402

s131 = import_module("02_correccion_area_por_angulo")
LAM, KW, AREA = pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2


def L(t):
    return C1_PLANCK / (LAM ** 5 * (math.exp(C2_PLANCK / (LAM * t)) - 1.0))


def vrp(bt, tb):
    return KW * AREA * max(L(bt) - L(tb), 0.0) / 1e6


d = json.load(open(AQUI.parent / "d_pasadas_salida.json", encoding="utf-8"))
crudos = {(r["sensor"], r["datetime_utc"]): r
          for r in json.load(open(ROOT / "data" / "mirova_equivalent" / "Tupungatito.json", encoding="utf-8"))["records"]}
leyes = {"f=1": lambda z: 1.0, "f_modelo (B)": s131.f_modelo, "f_lineal (C)": s131.f_lineal,
         "raíz de f_modelo": lambda z: math.sqrt(s131.f_modelo(z))}


def cierra(pix, t_bg, obj):
    if sum(vrp(p["bt_k"], t_bg - 60.0) for p in pix) < obj:
        return None
    lo, hi = -30.0, 60.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if sum(vrp(p["bt_k"], t_bg - mid) for p in pix) >= obj:
            hi = mid
        else:
            lo = mid
    return hi


out = []
P = out.append
P("fondo que cierra (K bajo la mediana del anillo), mediana por pasada; None contado como +inf; (n sin solución)")
for nombre, ley in leyes.items():
    por = {}
    for b in ("<30", "30-50", ">=50"):
        vals = []
        for f in d["pasadas"]:
            if f["banda"] != b:
                continue
            r = crudos[(f["sensor"], f["pasada"])]
            pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= 7.0]
            vals.append(cierra(pix, f["t_bg"], f["M"] / ley(f["cenital"])))
        n_none = sum(1 for v in vals if v is None)
        por[b] = (st.median([math.inf if v is None else v for v in vals]), n_none, len(vals))
    P(f"  {nombre:18s} " + "  ".join(f"{b}: {m:5.1f} ({nn}/{n})" for b, (m, nn, n) in por.items()))
P("")
P("factor de área medio por banda (mediana sobre las pasadas):")
for nombre, ley in leyes.items():
    P(f"  {nombre:18s} " + "  ".join(
        f"{b}: {st.median(ley(f['cenital']) for f in d['pasadas'] if f['banda'] == b):.2f}" for b in ("<30", "30-50", ">=50")))
txt = "\n".join(out)
print(txt)
(AQUI / "v5_fondo_que_cierra_modelos_salida.txt").write_text(txt + "\n", encoding="utf-8")
