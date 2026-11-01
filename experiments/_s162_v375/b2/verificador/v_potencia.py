import json, sys, collections, io
import numpy as np
from pathlib import Path
E=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375")
sys.path.insert(0,str(E))
import evaluar as EV
bc=json.loads((E/"objetivos_v375_bc.json").read_text(encoding="utf-8"))
b2=json.loads((E/"b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]
N={h:v["N"] for h,v in bc["meta"]["estratos"]["neg_resto"].items()}
fuera={1019,1184,1192,1232,1318,1403,1485,1556,1601,1611,1673}
n162=collections.Counter(o["estrato"] for o in bc["pasadas"] if o["clase"]=="neg_resto" and o["id"] not in fuera)
ev162=collections.Counter({"Lastarria|z>40":2,"Tupungatito|z<=40":1,"Llaima|z>40":1})
nb=collections.Counter(o["estrato"] for o in b2)
H=sorted(N)
NP,NR=133,3323; VARA=NP/(NP+NR); PUB_HI=0.3652
def decide(k,n,z=1.96):
    # replica evaluar: p ponderada, Kish, Wilson
    w=np.array([N[h]/n[h] for h in H if n[h]]); kk=np.array([k[h]/n[h] for h in H if n[h]])  # fraccion publica por estrato
    # tasa_ponderada: sum(w*x)/sum(w) con x binario por fila; equivale a sum_h N_h*(k_h/n_h)/sum N_h(cubiertos)
    sw=sum(N[h] for h in H if n[h]); p=sum(N[h]*k[h]/n[h] for h in H if n[h])/sw
    rows_w=np.concatenate([[N[h]/n[h]]*n[h] for h in H if n[h]])
    ne=rows_w.sum()**2/(rows_w**2).sum()
    lo,hi=EV.wilson(p*ne,ne,z)
    tot=(NP*PUB_HI+NR*hi)/(NP+NR)
    return tot<VARA, p, hi
rng=np.random.default_rng(7)
print("rate 1: baseline (S162 solo)", decide(ev162,n162))
def sim(prate, lastarria=None, m_obs=0.9725, reps=3000):
    ok=ok2=0
    for _ in range(reps):
        k=collections.Counter(ev162); n=collections.Counter(n162)
        for h in H:
            nn=rng.binomial(nb[h],m_obs)   # no observadas ~2.75%
            p=prate if not(lastarria and h.startswith("Lastarria")) else lastarria
            k[h]+=rng.binomial(nn,p); n[h]+=nn
        d,_,_=decide(k,n); ok+=d
        d2,_,_=decide(k,n,2.241) if False else (None,0,0)
    return ok/reps
for p in (0.005,0.0075,0.0095,0.0116,0.014,0.017,0.02):
    print(f"tasa {p:.4f}: decide {sim(p):.3f} | Lastarria 20%: {sim(p,0.20):.3f}")

print("--- regla vs estricta")
def sim2(prate, reps=3000):
    a=b=c=0
    for _ in range(reps):
        k=collections.Counter(ev162); n=collections.Counter(n162)
        for h in H:
            nn=rng.binomial(nb[h],0.9725); k[h]+=rng.binomial(nn,prate); n[h]+=nn
        d,_,_=decide(k,n)
        # estricta: PUB_HI con z 2,241 sobre 31/113
        sw=sum(N[h] for h in H if n[h]); p=sum(N[h]*k[h]/n[h] for h in H if n[h])/sw
        rows_w=np.concatenate([[N[h]/n[h]]*n[h] for h in H if n[h]]); ne=rows_w.sum()**2/(rows_w**2).sum()
        hi=EV.wilson(p*ne,ne,2.241)[1]
        pubs=EV.wilson(31,113,2.241)[1]
        e=(NP*pubs+NR*hi)/(NP+NR)<VARA
        a+=d; b+=(d and not e); c+=e
    return a/reps,b/reps,c/reps
for p in (0.005,0.0075,0.0095,0.0116,0.014):
    print(p, "regla, regla&!estricta, estricta:", sim2(p))
print("PUB_HI estricto", EV.wilson(31,113,2.241)[1], "normal", EV.wilson(31,113,1.96)[1])
