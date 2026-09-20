# -*- coding: utf-8 -*-
"""V-03: AUC de test1_k_observed con etiqueta 'MIROVA publico ALERTA (vol, fecha+-1 dia, sensor)'. Poblacion S116: recapture>0 & summit & pc<=inner.
(1) roto? control: AUC de una variable barajada debe dar ~0,5 (nulo), y AUC de la propia etiqueta =1. (2) muerto? se imprime n_pos/n_neg por estrato.
Ventana S116: hasta 2026-06-25 aprox (la sesion S116); se mide esa y la total 2026."""
import io, sys, random, datetime as dt
from collections import defaultdict
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Tupungatito": 7, "PuyehueCordonCaulle": 20}
D = cargar(); REF = referencia(incluir_ocr=False)
K = set()
for f in REF:
    if f["tipo"] != "ALERTA_TERMICA": continue
    d0 = dt.date.fromisoformat(f["fecha"])
    for k in (-1, 0, 1): K.add((f["vol"], str(d0 + dt.timedelta(days=k)), f["b"]))
def auc(pos, neg):
    allv = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg]); n = len(allv); ranks = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1][0] == allv[i][0]: j += 1
        for k in range(i, j + 1): ranks[k] = (i + j) / 2 + 1
        i = j + 1
    rp = sum(r for r, (_, l) in zip(ranks, allv) if l == 1)
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
random.seed(146)
for w in (("2026-01-29", "2026-06-25"), ("2026-01-29", "2026-09-19")):
    rows = []
    for v in VOLS:
        for r in D[v]:
            f = r["datetime_utc"][:10]
            if not (w[0] <= f <= w[1]): continue
            pc = r.get("primary_cluster") or {}
            if (r.get("diag_n_second_pass_recapture") or 0) > 0 and r.get("distance_class") == "summit" and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER.get(v, 5):
                b = bucket(r["sensor"]); rows.append((v, b, (v, f, b) in K, r.get("test1_k_observed") or 0.0, bool(r.get("triggered_test1"))))
    print("\nventana", w, "n", len(rows), "positivos", sum(x[2] for x in rows), f"({100*sum(x[2] for x in rows)/len(rows):.1f}%)")
    def rep(nombre, sub):
        p = [x[3] for x in sub if x[2]]; n = [x[3] for x in sub if not x[2]]
        if len(p) < 5 or len(n) < 5: print(f"  {nombre:28s} SIN DATO (pos {len(p)}, neg {len(n)})"); return
        a = auc(p, n); nulos = []
        lab = [x[2] for x in sub]; val = [x[3] for x in sub]
        for _ in range(200):
            random.shuffle(lab); nulos.append(auc([x for x, l in zip(val, lab) if l], [x for x, l in zip(val, lab) if not l]))
        nulos.sort()
        ind = auc([1.0 if x[4] else 0.0 for x in sub if x[2]], [1.0 if x[4] else 0.0 for x in sub if not x[2]])
        print(f"  {nombre:28s} pos {len(p):5d} neg {len(n):5d} AUC {a:.3f} | nulo barajado p2.5-p97.5 [{nulos[5]:.3f}, {nulos[194]:.3f}] | AUC del indicador binario triggered_test1: {ind:.3f} | frac k==0: {sum(1 for x in sub if x[3]==0)/len(sub):.2f}")
    rep("GLOBAL", rows)
    for b in ("modis", "v750", "v375"): rep("sensor " + b, [x for x in rows if x[1] == b])
    # control: usar el SENSOR como 'discriminante' (1 si v375): si da AUC alto, la etiqueta esta confundida con el sensor
    p = [1.0 if x[1] == "v375" else 0.0 for x in rows if x[2]]; n = [1.0 if x[1] == "v375" else 0.0 for x in rows if not x[2]]
    print("  control de confusion: AUC de 'es VIIRS 375' contra la misma etiqueta:", round(auc(p, n), 3))
    rep("solo k>0, global", [x for x in rows if x[3] > 0])
    for b in ("v750", "v375"): rep("solo k>0, " + b, [x for x in rows if x[3] > 0 and x[1] == b])
