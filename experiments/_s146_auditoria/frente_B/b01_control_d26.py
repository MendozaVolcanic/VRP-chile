# -*- coding: utf-8 -*-
"""S146 B control positivo D26: repite que_rama_manda.py pero leyendo TAMBIEN diag_mu_deti/diag_sd_deti (Test 3).
1. Si lo medido estuviera roto (el piso gobernara tambien el Test 3), saldria ~100 % como en dNTI: la prueba lo mostraria.
2. Si el instrumento estuviera muerto (campos ausentes), n=0 y se imprime; no se confunde con 0 %.
Read-only."""
import os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
C1S, C2S = 0.003, 5.0
T = ["Villarrica","Lascar","Isluga","NevadosDeChillan","Llaima","Chaiten","Copahue","Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]
def b(s):
    if not s: return None
    return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375") if s.startswith("VIIRS") else None
agg = {}
for v in T:
    d = json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8")); recs = d.get("records", d)
    for r in recs:
        k = b(r.get("sensor"))
        if not k: continue
        for t in ("dnti","deti"):
            mu, sd = r.get("diag_mu_"+t), r.get("diag_sd_"+t)
            if not isinstance(mu,(int,float)) or not isinstance(sd,(int,float)): continue
            a = agg.setdefault((k,t),[0,0]); a[0]+=1; a[1]+= (C1S < mu + C2S*sd)
for (k,t),(n,p) in sorted(agg.items()):
    print(f"{k:6s} {t}: n={n} manda_piso_cumbre={p} ({100*p/n:.1f}%)  manda_sigma={100-100*p/n:.1f}%")
