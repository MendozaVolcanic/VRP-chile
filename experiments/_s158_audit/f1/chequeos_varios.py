# -*- coding: utf-8 -*-
"""F1 (S158): chequeos chicos. (a) nti_max contra -0,7 y -0,8 en la ventana K, sin agrupar. (b) filtros de artefacto
del tablero sobre V750. (c) alertas diurnas de VIIRS 750 en la tabla de MIROVA (nosotros rechazamos todo VIIRS
diurno). (d) orden de magnitud del sesgo de la ida y vuelta LUT -> Planck monocromática a 4,05 µm, con una
respuesta espectral de M13 SUPUESTA rectangular (3,973 a 4,128 µm): SOSPECHA, no medición del LUT real.
Uso: python -B experiments/_s158_audit/f1/chequeos_varios.py
"""
import io, json, math, os, sys
from collections import Counter
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.store import _solar_elevation
VOLS = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
        "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
pub = json.load(open(os.path.join(AQUI, "pub_v750.json"), encoding="utf-8"))
P = {(p["v"], p["t"], p["s"]): p for p in pub}
print("(a) nti_max en ventana K (>= 2026-09-18), por record:")
c = Counter()
for v in VOLS:
    for r in json.load(open(os.path.join(RAIZ, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        if not str(r.get("sensor", "")).endswith("_750") or r["datetime_utc"] < "2026-09-18":
            continue
        nm = r.get("nti_max")
        if nm is None:
            continue
        if nm > -0.7:
            c["> -0.7"] += 1
            print("    ", v, r["datetime_utc"], r["sensor"], "nti_max", nm, "n_nti_path", r.get("n_nti_path"),
                  "pub", P[(v, r["datetime_utc"], r["sensor"])]["pub"])
        elif nm > -0.8:
            c["(-0.8, -0.7]"] += 1
print("   ", dict(c))
print("(b) filtros de artefacto del tablero en V750, corpus entero: art=True con eq>0:",
      sum(1 for p in pub if p["art"] and p["eq"] > 0), " eq>0:", sum(1 for p in pub if p["eq"] > 0),
      " pub>0:", sum(1 for p in pub if p["pub"] > 0), " valid y pub==0:", sum(1 for p in pub if p["valid"] and p["pub"] == 0))
ref = pd.read_csv(os.path.join(RAIZ, "latest_consolidado.csv"))
ref = ref[(ref["Sensor"] == "VIIRS")]
import yaml
cfg = {x["name"]: x for x in yaml.safe_load(open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
ALIAS = {"Planchon-Peteroa": "PlanchonPeteroa", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "NevadosDeChillan"}
cc = Counter()
for _, f in ref.iterrows():
    v = ALIAS.get(f["Volcan"], f["Volcan"])
    if v not in cfg or f["Fecha_Satelite_UTC"] < "2026-03-01":
        continue
    el = _solar_elevation(cfg[v]["lat"], cfg[v]["lon"], datetime.strptime(f["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M"))
    cc[(f["Tipo_Registro"], "dia" if el > 0 else "noche")] += 1
print("(c) filas de la tabla VIIRS 750 desde 2026-03-01 por tipo y día/noche:", dict(cc))
C1, C2 = 1.191042e8, 14388.0
B = lambda lam, T: C1 / (lam ** 5 * (np.exp(C2 / (lam * T)) - 1))
lam = np.linspace(3.973, 4.128, 400)
print("(d) SRF rectangular SUPUESTA de M13: razón Planck(4,05; T) / radiancia de banda(T)")
for T in (240, 260, 280, 300, 350, 400, 600):
    Lb = np.trapezoid(B(lam, T), lam) / (lam[-1] - lam[0])
    print(f"    T={T} K  razón {B(4.05, T) / Lb:.5f}")
