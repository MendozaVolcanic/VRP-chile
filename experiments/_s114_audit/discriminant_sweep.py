#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 brainstorming D11 — barrido sistematico de discriminantes per-record.

OBJETIVO: encontrar un campo (o combo) que separe FOCO REAL (Lascar far->summit, desierto)
de A69 DIFUSO (nevados far->summit RUTINA). "Probar todo y descartar" (pedido Nicolas).

Metrica: AUC (Mann-Whitney U / (n_pos*n_neg)) = P(un Lascar tenga mayor valor que un nevado).
  AUC ~1.0 o ~0.0 = separa fuerte. AUC ~0.5 = inutil. |AUC-0.5| = poder de separacion.
Tambien: cuanto del negativo (A69) descarto conservando >=90% del positivo (Lascar).
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
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
NEVADOS = ["Tupungatito", "NevadosDeChillan", "Villarrica", "Copahue", "Lastarria",
           "PlanchonPeteroa", "Llaima", "Isluga", "PuyehueCordonCaulle", "Chaiten"]

# estado MIROVA MODIS por noche + magnitud VIIRS375 co-val
mir = defaultdict(lambda: {"a": 0, "r": 0})
for r in csv.DictReader(open(CONS, encoding="utf-8")):
    if r["Volcan"] in VOLS.values() and r["Sensor"] == "MODIS":
        k = (r["Volcan"], r["Fecha_Satelite_UTC"][:10])
        if r["Tipo_Registro"] == "ALERTA_TERMICA": mir[k]["a"] += 1
        elif r["Tipo_Registro"] == "RUTINA": mir[k]["r"] += 1

# index records + VIIRS375 magnitud por dia
recidx, v375mag = {}, defaultdict(dict)
for vj in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vj + ".json"), encoding="utf-8"))
    inner = INNER[vj]; ri = {}
    for rec in d["records"]:
        s = rec.get("sensor", "")
        if s.startswith("MODIS"):
            ri[rec.get("datetime_utc")] = rec
        elif s.startswith("VIIRS") and not s.endswith("_750"):
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0; cd = pc.get("centroid_dist_km")
            if 0 < vrp <= 50000 and cd is not None and cd <= inner:
                dt = rec.get("datetime_utc")
                if dt: v375mag[vj][dt[:10]] = max(v375mag[vj].get(dt[:10], 0), vrp)
    recidx[vj] = ri

FEATURES = ["diag_n_first_pass_summit", "diag_n_first_pass_pixels", "diag_n_dnti_ctx_path",
            "diag_n_eti_path", "diag_n_nti_path", "diag_n_bt_path", "diag_n_second_pass_recapture",
            "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti", "diag_nti_max",
            "diag_nti_bg", "diag_nti_std", "diag_sigma_bg_k", "diag_roi_p95_k", "diag_t_max_dist_km",
            "t_max_k", "t_bg_k"]

def extract(rec, vj, date):
    pc = rec.get("primary_cluster") or {}
    f = {k: rec.get(k) for k in FEATURES}
    tmax, tbg = rec.get("t_max_k"), rec.get("t_bg_k")
    f["dT"] = (tmax - tbg) if (tmax is not None and tbg is not None) else None
    f["pc_n_pixels"] = pc.get("n_pixels")
    f["pc_vrp"] = pc.get("vrp_mw")
    f["v375_coval_mag"] = v375mag[vj].get(date, 0.0)  # 0 = VIIRS375 no vio foco
    return f

POS, NEG = [], []  # POS = Lascar far->summit (foco real); NEG = nevados far->summit RUTINA (A69)
for x in far:
    if x["sensor"] != "MODIS": continue
    rec = recidx[x["vol"]].get(x["datetime"])
    if not rec: continue
    feats = extract(rec, x["vol"], x["date"])
    st = "ALERTA" if mir[(VOLS[x["vol"]], x["date"])]["a"] else "RUTINA"
    if x["vol"] == "Lascar":
        POS.append(feats)
    elif x["vol"] in NEVADOS and st == "RUTINA":
        NEG.append(feats)

print("POS (Lascar far->summit, foco real): n=%d" % len(POS))
print("NEG (nevados RUTINA far->summit, A69): n=%d" % len(NEG))
print()

def auc(pos, neg, key):
    p = [r[key] for r in pos if r.get(key) is not None]
    n = [r[key] for r in neg if r.get(key) is not None]
    if len(p) < 5 or len(n) < 5: return None, len(p), len(n)
    # Mann-Whitney U via rank
    wins = ties = 0
    # O(n*m) ok (n<100, m<800)
    for a in p:
        for b in n:
            if a > b: wins += 1
            elif a == b: ties += 1
    return (wins + 0.5 * ties) / (len(p) * len(n)), len(p), len(n)

ALLF = FEATURES + ["dT", "pc_n_pixels", "pc_vrp", "v375_coval_mag"]
results = []
for k in ALLF:
    a, np_, nn_ = auc(POS, NEG, k)
    if a is None: continue
    mp = statistics.median([r[k] for r in POS if r.get(k) is not None])
    mn = statistics.median([r[k] for r in NEG if r.get(k) is not None])
    results.append((abs(a - 0.5), a, k, mp, mn, np_, nn_))

results.sort(reverse=True)
print("%-26s %5s  %8s %8s  %s" % ("FEATURE", "AUC", "med_POS", "med_NEG", "poder|AUC-.5|"))
print("-" * 75)
for power, a, k, mp, mn, np_, nn_ in results:
    flag = "  <== SEPARA" if power > 0.30 else ("  ~ debil" if power > 0.15 else "")
    print("%-26s %.3f  %8.3f %8.3f   %.3f%s" % (k, a, mp, mn, power, flag))
