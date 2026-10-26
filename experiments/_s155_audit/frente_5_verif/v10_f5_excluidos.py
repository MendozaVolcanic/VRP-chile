# -*- coding: utf-8 -*-
"""Verificador F5, paso 10: que pixeles deja FUERA F5' en V375 (pareados), a que distancia del pico y con
que energia. Corrige una afirmacion propia del borrador ("solo deja fuera lo que esta a > 5 km").
Pregunta 1: si F5' no excluyera nada, la lista saldria vacia. Denominador: 51 pasadas V375 pareadas."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v03_fondo_cero_v375 import f5_conjunto, hav
A = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(A, "pares_remoto.json"), encoding="utf-8"))
d = json.load(open(os.path.join(A, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
idx = {(r["datetime_utc"][:16], r["sensor"]): r for r in d["records"]}
tot_ex = tot_ex_cerca = tot_pub = 0.0; n = 0
for f in P:
    if f["b"] != "VIIRS375":
        continue
    r = idx[(f["t"], f["sensor"])]; ap = r["anomaly_pixels"]; s = f5_conjunto(ap, r["primary_cluster"])
    pk = max(s, key=lambda p: p["vrp_mw"])
    ex = [p for p in ap if p not in s]
    tot_pub += sum(p["vrp_mw"] for p in s)
    for p in ex:
        dpk = hav(p["lat"], p["lon"], pk["lat"], pk["lon"])
        tot_ex += p["vrp_mw"]; n += 1
        if dpk <= 5: tot_ex_cerca += p["vrp_mw"]
        print("%s cenit %4.1f  excluido a %5.2f km del pico, bt %.1f, vrp %.2f (F5 %.2f, MIROVA %.2f)" % (f["t"], f["zen"], dpk, p["bt_k"], p["vrp_mw"], sum(q["vrp_mw"] for q in s), f["mir"]))
print("pixeles excluidos=%d; energia excluida %.2f MW (a <=5 km del pico %.2f) frente a %.2f MW publicados en las 51" % (n, tot_ex, tot_ex_cerca, tot_pub))
