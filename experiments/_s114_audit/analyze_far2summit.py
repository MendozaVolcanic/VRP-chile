#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 — Discriminante real-vs-A69 para los far->summit MODIS.

POR QUE: el campo difuso MODIS (A69) genera clusters crateriana espurios casi cada noche
  (gradiente topografico crater-frio/valle-tibio captado por MIR absoluto). La lava real
  rompe la simetria espectral -> NTI sube. A80: nti_max plano (~-0.9) = artefacto; nti_max
  alto = senal genuina. Cruzamos cada far->summit con (a) estado MIROVA esa noche+sensor
  (ALERTA/RUTINA/nada) y (b) nti_max, para ver si el discriminante separa Lascar (legitimo,
  D12) de NdC/Villarrica/Tupun (A69 residual, veredicto S111).
"""
import csv, json, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
res = json.load(open(os.path.join(HERE, "parity_s114_result.json"), encoding="utf-8"))
far = res["far2summit"]

VOLS = {"Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
        "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
        "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
        "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}

# estado MIROVA por (vol_cons, sensor, date)
mir = defaultdict(lambda: {"alerta": 0, "rutina": 0})
with open(CONS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["Volcan"] not in VOLS.values():
            continue
        sens = r["Sensor"]
        sens = "VIIRS750" if sens == "VIIRS" else sens
        key = (r["Volcan"], sens, r["Fecha_Satelite_UTC"][:10])
        if r["Tipo_Registro"] == "ALERTA_TERMICA":
            mir[key]["alerta"] += 1
        elif r["Tipo_Registro"] == "RUTINA":
            mir[key]["rutina"] += 1


def mstate(vol_json, sensor, date):
    m = mir.get((VOLS[vol_json], sensor, date), {"alerta": 0, "rutina": 0})
    if m["alerta"]:
        return "ALERTA"
    if m["rutina"]:
        return "RUTINA"
    return "nada"


# clasificar far->summit por vol y estado MIROVA + nti_max
print(">>> far->summit por VOL x estado-MIROVA-esa-noche (nti_max median) <<<")
print("  %-18s %8s %8s %8s   %s" % ("VOL", "ALERTA", "RUTINA", "nada", "nti_max med [ALERTA|RUTINA|nada]"))
per_vol = defaultdict(lambda: {"ALERTA": [], "RUTINA": [], "nada": []})
for x in far:
    st = mstate(x["vol"], x["sensor"], x["date"])
    per_vol[x["vol"]][st].append(x.get("nti_max"))


def med(xs):
    xs = [v for v in xs if v is not None]
    return round(statistics.median(xs), 3) if xs else None


for vol in sorted(per_vol, key=lambda v: -sum(len(s) for s in per_vol[v].values())):
    d = per_vol[vol]
    print("  %-18s %8d %8d %8d   [%s | %s | %s]" % (
        vol, len(d["ALERTA"]), len(d["RUTINA"]), len(d["nada"]),
        med(d["ALERTA"]), med(d["RUTINA"]), med(d["nada"])))

# distribucion nti_max global ALERTA vs (RUTINA+nada)
alerta_nti = [x.get("nti_max") for x in far if mstate(x["vol"], x["sensor"], x["date"]) == "ALERTA" and x.get("nti_max") is not None]
noise_nti = [x.get("nti_max") for x in far if mstate(x["vol"], x["sensor"], x["date"]) != "ALERTA" and x.get("nti_max") is not None]
print()
print(">>> DISCRIMINANTE nti_max: ALERTA-MIROVA vs RUTINA/nada <<<")


def stats(xs):
    if not xs:
        return "n=0"
    xs = sorted(xs)
    return "n=%d min=%.3f p25=%.3f med=%.3f p75=%.3f max=%.3f" % (
        len(xs), xs[0], xs[len(xs)//4], statistics.median(xs), xs[3*len(xs)//4], xs[-1])


print("  far->summit en noche ALERTA  :", stats(alerta_nti))
print("  far->summit en noche RUT/nada:", stats(noise_nti))

# si pusieramos un umbral nti_max, cuanto separa?
for thr in [-0.9, -0.85, -0.8, -0.7, -0.6, -0.5, -0.4]:
    keep_a = sum(1 for v in alerta_nti if v >= thr)
    keep_n = sum(1 for v in noise_nti if v >= thr)
    print("    thr nti>=%.2f: conserva %d/%d ALERTA, deja pasar %d/%d RUT/nada" % (
        thr, keep_a, len(alerta_nti), keep_n, len(noise_nti)))

# final_hotspot_source de los far->summit
src = defaultdict(int)
for x in far:
    src[x.get("final_hotspot_source")] += 1
print()
print(">>> final_hotspot_source de far->summit <<<", dict(src))
