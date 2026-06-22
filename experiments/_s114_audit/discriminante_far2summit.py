#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 — Discriminante real-vs-A69 para far->summit MODIS, con CAMPOS CORRECTOS (A48).

Campos persistidos del record MODIS (verificados, no inventados):
  diag_nti_max, diag_nti_bg, diag_nti_std, t_max_k, t_bg_k, diag_n_first_pass_summit,
  primary_cluster.{n_pixels, focal_magnitude}.
Discriminantes candidatos a separar Lascar (legitimo D12) de nevados (A69):
  (1) diag_nti_max (A80: artefacto topografico ~piso; lava rompe simetria espectral)
  (2) dT = t_max_k - t_bg_k (A12/A69: foco real ΔT alto; difuso ΔT bajo)
  (3) diag_n_first_pass_summit (gate S111 — necesario no suficiente)
  (4) CO-VALIDACION VIIRS375 misma-noche (el "escalon mas" que S111 nombro):
      ¿hay foco crateriano VIIRS375 (pc.vrp>0, centroid<=inner) esa noche?
Cruzado con estado MIROVA-MODIS de la noche (ALERTA/RUTINA/nada).
"""
import csv, json, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
far = json.load(open(os.path.join(HERE, "parity_s114_result.json"), encoding="utf-8"))["far2summit"]

VOLS = {"Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
        "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
        "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
        "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}

# estado MIROVA MODIS por (vol_cons, date)
mir = defaultdict(lambda: {"alerta": 0, "rutina": 0})
with open(CONS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["Volcan"] not in VOLS.values() or r["Sensor"] != "MODIS":
            continue
        key = (r["Volcan"], r["Fecha_Satelite_UTC"][:10])
        if r["Tipo_Registro"] == "ALERTA_TERMICA":
            mir[key]["alerta"] += 1
        elif r["Tipo_Registro"] == "RUTINA":
            mir[key]["rutina"] += 1


def mstate(vol_json, date):
    m = mir.get((VOLS[vol_json], date), {"alerta": 0, "rutina": 0})
    return "ALERTA" if m["alerta"] else ("RUTINA" if m["rutina"] else "nada")


# pre-cargar JSON por vol: index record MODIS por datetime + set de noches con summit VIIRS375
recidx = {}          # vol -> {datetime: rec}
viirs375_summit = defaultdict(set)  # vol -> {date con foco VIIRS375 al crater}
for vjson in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vjson + ".json"), encoding="utf-8"))
    inner = INNER[vjson]
    ri = {}
    for rec in d["records"]:
        s = rec.get("sensor", "")
        if s.startswith("MODIS"):
            ri[rec.get("datetime_utc")] = rec
        elif s.startswith("VIIRS") and not s.endswith("_750"):  # VIIRS375 I-band (A48)
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cd = pc.get("centroid_dist_km")
            if 0 < vrp <= 50000 and cd is not None and cd <= inner:
                dt = rec.get("datetime_utc")
                if dt:
                    viirs375_summit[vjson].add(dt[:10])
    recidx[vjson] = ri

# enriquecer cada far->summit
rows = []
for x in far:
    if x["sensor"] != "MODIS":
        continue
    rec = recidx[x["vol"]].get(x["datetime"])
    if rec is None:
        continue
    pc = rec.get("primary_cluster") or {}
    tmax, tbg = rec.get("t_max_k"), rec.get("t_bg_k")
    rows.append({
        "vol": x["vol"], "date": x["date"], "state": mstate(x["vol"], x["date"]),
        "pc_vrp": pc.get("vrp_mw"), "n_pixels": pc.get("n_pixels"),
        "diag_nti_max": rec.get("diag_nti_max"), "diag_nti_bg": rec.get("diag_nti_bg"),
        "dT": (tmax - tbg) if (tmax is not None and tbg is not None) else None,
        "fps": rec.get("diag_n_first_pass_summit"),
        "viirs375_covalid": x["date"] in viirs375_summit[x["vol"]],
    })


def dist(xs, label):
    xs = sorted(v for v in xs if v is not None)
    if not xs:
        return label + ": n=0"
    return "%s: n=%d min=%.2f p25=%.2f med=%.2f p75=%.2f max=%.2f" % (
        label, len(xs), xs[0], xs[len(xs)//4], statistics.median(xs), xs[min(len(xs)-1, 3*len(xs)//4)], xs[-1])


for key, name in [("ALERTA", "noche ALERTA-MIROVA-MODIS (legitimo)"), ("RUTINA", "noche RUTINA (candidato A69)")]:
    sub = [r for r in rows if r["state"] == key]
    print("\n=== far->summit MODIS en %s  (n=%d) ===" % (name, len(sub)))
    print(" ", dist([r["diag_nti_max"] for r in sub], "diag_nti_max"))
    print(" ", dist([r["dT"] for r in sub], "dT=tmax-tbg "))
    print(" ", dist([r["fps"] for r in sub], "first_pass_summit"))
    print(" ", dist([r["pc_vrp"] for r in sub], "pc.vrp_mw  "))
    cov = sum(1 for r in sub if r["viirs375_covalid"])
    print("  VIIRS375 co-valida (mismo dia foco crater): %d/%d (%.0f%%)" % (cov, len(sub), 100*cov/len(sub) if sub else 0))

# CO-VALIDACION como discriminante: matriz state x covalid
print("\n=== MATRIZ: estado-MIROVA x co-validacion-VIIRS375 ===")
mtx = defaultdict(int)
for r in rows:
    mtx[(r["state"], r["viirs375_covalid"])] += 1
print("  %-8s  VIIRS375-coval=True  VIIRS375-coval=False" % "estado")
for st in ["ALERTA", "RUTINA", "nada"]:
    print("  %-8s  %18d  %19d" % (st, mtx[(st, True)], mtx[(st, False)]))

# por vol: cuantos far->summit, cuantos co-validados VIIRS375
print("\n=== por VOL: far->summit MODIS y co-validacion VIIRS375 ===")
pv = defaultdict(lambda: {"n": 0, "alerta": 0, "coval": 0, "alerta_coval": 0})
for r in rows:
    p = pv[r["vol"]]
    p["n"] += 1
    if r["state"] == "ALERTA":
        p["alerta"] += 1
    if r["viirs375_covalid"]:
        p["coval"] += 1
    if r["state"] == "ALERTA" and r["viirs375_covalid"]:
        p["alerta_coval"] += 1
print("  %-18s %5s %7s %7s %12s" % ("VOL", "n", "ALERTA", "coval", "ALERTA&coval"))
for v in sorted(pv, key=lambda v: -pv[v]["n"]):
    p = pv[v]
    print("  %-18s %5d %7d %7d %12d" % (v, p["n"], p["alerta"], p["coval"], p["alerta_coval"]))

json.dump(rows, open(os.path.join(HERE, "discriminante_result.json"), "w", encoding="utf-8"), indent=1)
print("\nWROTE discriminante_result.json")
