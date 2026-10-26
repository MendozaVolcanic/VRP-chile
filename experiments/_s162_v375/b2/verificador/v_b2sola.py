import sys, numpy as np
sys.path.insert(0,r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375")
import evaluar as EV
NP,NR=133,3323; V=NP/(NP+NR); PUB=0.3652
rng=np.random.default_rng(3)
for p in (0.005,0.0075,0.0095,0.0116,0.014):
    n=583
    ok=0;okz=0
    for _ in range(4000):
        k=rng.binomial(n,p)
        hi=EV.wilson(k,n)[1]; ok+=(NP*PUB+NR*hi)/(NP+NR)<V
        hi=EV.wilson(k,n,2.241)[1]; okz+=(NP*0.3765+NR*hi)/(NP+NR)<V
    print(p,"B2 sola decide",ok/4000,"estricta",okz/4000)
