import json, math, collections, numpy as np
R=r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375"
bc=json.load(open(R+r"\objetivos_v375_bc.json",encoding="utf-8"))["pasadas"]
b2=json.load(open(R+r"\b2\objetivos_v375_b2.json",encoding="utf-8"))
m=b2["meta"]["estratos_neg_resto"]
ev={1562,1704,1189,1473}
n162=collections.Counter(); k162=collections.Counter()
# n ok S162 por estrato: usar todas menos 11 no observadas (ids fuera del granulo); aproximacion: todas las neg_resto S162
for o in bc:
    if o["clase"]=="neg_resto": n162[o["estrato"]]+=1; k162[o["estrato"]]+= o["id"] in ev
print({h:(k162[h],n162[h]) for h in k162 if k162[h]})
def wilson(p,n,z=1.96):
    d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(max(p*(1-p)/n+z*z/(4*n*n),0))/d; return c+h
NP,NR=133,3323; VARA=NP/(NP+NR); PUBHI=0.3652
H=sorted(m); N=np.array([m[h]["N"] for h in H],float); nb=np.array([m[h]["n_b2"] for h in H])
w=N/nb; ne=w.sum()**0+ (nb*w).sum()**2/(nb*w**2).sum()
rng=np.random.default_rng(1)
def potencia(modo, S=20000, pool_mu=None):
    ok=0
    a=np.array([k162[h]+0.5 for h in H]); b=np.array([n162[h]-k162[h]+0.5 for h in H])
    for _ in range(S):
        if modo=="nopool": p=rng.beta(a,b)
        elif modo=="pool":
            mu=rng.beta(4.5,385.5); p=np.full(len(H),mu)
        elif modo=="partial":  # media comun + desvio por estrato (gamma con CV 1)
            mu=rng.beta(4.5,385.5); p=np.minimum(mu*rng.gamma(1.0,1.0,len(H)),1)
        k=rng.binomial(nb,p)
        ph=(w*k).sum()/N.sum()
        hi=wilson(ph,ne)
        ok+= (NP*PUBHI+NR*hi)/(NP+NR)<VARA
    return ok/S
for modo in ("pool","partial","nopool"):
    print(modo, round(potencia(modo),3))
