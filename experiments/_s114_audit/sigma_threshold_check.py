#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 FRENTE B — chequeo OPERACIONAL de las variantes que dieron AUC>0.80.
AUC alto != separable por un umbral unico. La pregunta MISSION: existe un umbral T
(mismo para todos los vols MODIS) que conserve >=90% Lascar-ALERTA y corte >=50% nevados?
"""
import json, csv, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
far = json.load(open(os.path.join(HERE, "parity_s114_result.json"), encoding="utf-8"))["far2summit"]

VOLS = {"Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
        "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
        "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
        "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
NEVADOS = ["Tupungatito", "NevadosDeChillan", "Villarrica", "Copahue", "Lastarria",
           "PlanchonPeteroa", "Llaima", "Isluga", "PuyehueCordonCaulle", "Chaiten"]

mir = defaultdict(lambda: {"a": 0})
for r in csv.DictReader(open(CONS, encoding="utf-8")):
    if r["Volcan"] in VOLS.values() and r["Sensor"] == "MODIS":
        if r["Tipo_Registro"] == "ALERTA_TERMICA":
            mir[(r["Volcan"], r["Fecha_Satelite_UTC"][:10])]["a"] += 1

recidx = {}
for vj in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vj + ".json"), encoding="utf-8"))
    recidx[vj] = {rec.get("datetime_utc"): rec for rec in d["records"]
                  if rec.get("sensor", "").startswith("MODIS")}


def fnum(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def vb(rec):
    nm, nb = fnum(rec.get("diag_nti_max")), fnum(rec.get("diag_nti_bg"))
    sd = fnum(rec.get("diag_sd_dnti"))
    return (nm - nb) / sd if (nm is not None and nb is not None and sd and sd > 0) else None


def vd(rec):
    tm, tb = fnum(rec.get("t_max_k")), fnum(rec.get("t_bg_k"))
    sg = fnum(rec.get("diag_sigma_bg_k"))
    return (tm - tb) / sg if (tm is not None and tb is not None and sg and sg > 0) else None


POS, NEG = [], []
for x in far:
    if x["sensor"] != "MODIS":
        continue
    rec = recidx[x["vol"]].get(x["datetime"])
    if not rec:
        continue
    b, dd = vb(rec), vd(rec)
    st_a = mir[(VOLS[x["vol"]], x["date"])]["a"]
    row = {"vol": x["vol"], "b": b, "d": dd}
    if x["vol"] == "Lascar" and st_a:
        POS.append(row)
    elif x["vol"] in NEVADOS and st_a == 0:
        NEG.append(row)

print("nP=%d nN=%d" % (len(POS), len(NEG)))
for key, label in [("b", "(NTImax-NTIbg)/sd_dnti"), ("d", "(Tmax-Tbg)/sigma_bg_k")]:
    pv = sorted(r[key] for r in POS if r[key] is not None)
    nv = [r[key] for r in NEG if r[key] is not None]
    print("\n=== VARIANT %s = %s ===" % (key, label))
    print(" POS min/med/max: %.3f / %.3f / %.3f" % (pv[0], statistics.median(pv), pv[-1]))
    print(" NEG min/med/max: %.3f / %.3f / %.3f" % (min(nv), statistics.median(nv), max(nv)))
    # umbral que conserva >=90% POS (= corta <=10% Lascar): el percentil-10 de POS
    import math
    i = 0.10 * (len(pv) - 1)
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    T = pv[lo] if lo == hi else pv[lo] + (pv[hi] - pv[lo]) * (i - lo)
    keep_pos = sum(1 for v in pv if v >= T)
    cut_neg = sum(1 for v in nv if v < T)
    print(" T(conserva 90%% Lascar) = %.3f" % T)
    print("   Lascar conservados: %d/%d (%.0f%%)" % (keep_pos, len(pv), 100 * keep_pos / len(pv)))
    print("   nevados CORTADOS:   %d/%d (%.0f%%)" % (cut_neg, len(nv), 100 * cut_neg / len(nv)))
    # umbral simetrico: el que corta 50% nevados, cuanto Lascar pierde?
    nv_s = sorted(nv)
    Tmed = statistics.median(nv_s)
    keep_pos2 = sum(1 for v in pv if v >= Tmed)
    print(" T(=mediana nevados=%.3f): Lascar conservados %d/%d (%.0f%%)"
          % (Tmed, keep_pos2, len(pv), 100 * keep_pos2 / len(pv)))
