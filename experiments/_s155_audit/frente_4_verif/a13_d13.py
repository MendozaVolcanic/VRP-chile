# F4-13 (D13): de los records con cumulo de magnitud > 0, ¿que fraccion (records y MW) apaga la cerca dc != summit?
# Pareado C0 tag vs K main 18sep-17oct, por sensor. P1: si la cerca no existiera daria 0; P2: n impreso.
import json, collections
L=lambda f:[json.loads(x) for x in open(f,encoding="utf-8")]
M={(r["vol"],r["dt"],r["sensor"]):r for r in L("main_jul_oct.jsonl")}
c=collections.Counter()
for t in L("tag_c0_ventana.jsonl"):
    if t["noche"]>"2026-10-17": continue
    m=M.get((t["vol"],t["dt"],t["sensor"]))
    if not m or m["reg"]!="K": continue
    for nom,r in (("C0",t),("K",m)):
        v=r["pc_vrp"] or 0
        if v<=0: continue
        for b in (r["b"],"TODOS"):
            c[(nom,b,"n")]+=1; c[(nom,b,"mw")]+=v
            if r["dc"]!="summit": c[(nom,b,"n_cerca")]+=1; c[(nom,b,"mw_cerca")]+=v
for nom in ("C0","K"):
    for b in ("TODOS","VIIRS375","VIIRS750","MODIS"):
        n=c[(nom,b,"n")]
        print(nom,b,f"records {c[(nom,b,'n_cerca')]}/{n} | MW {c[(nom,b,'mw_cerca')]:.1f}/{c[(nom,b,'mw')]:.1f}")
