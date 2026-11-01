import sys, numpy as np
sys.path.insert(0,r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375")
import evaluar as EV
NP,NR=133,3323; V=NP/(NP+NR)
rng=np.random.default_rng(11)
def rechaza(kp,np_,kr,nr,z):
    return (NP*EV.wilson(kp,np_,z)[1]+NR*EV.wilson(kr,nr,z)[1])/(NP+NR)<V
for q in (0.2,0.3,0.4):
    r=(NP*(1-q))/NR   # tasa de neg_resto que deja el total EXACTAMENTE en la vara
    R=6000; a1=a2=a2s=any_=any_s=0
    for _ in range(R):
        kp=rng.binomial(113,q); k1=rng.binomial(389,r); k2=k1+rng.binomial(589,r)
        l1=rechaza(kp,113,k1,389,1.96); l2=rechaza(kp,113,k2,978,1.96); l2s=rechaza(kp,113,k2,978,2.241)
        a1+=l1; a2+=l2; any_+= (l1 or l2); any_s+= (l1 or l2s)
    print(f"q={q} r={r:.4f}: P(look1)={a1/R:.4f} P(look2 regular)={a2/R:.4f} P(alguna, regular)={any_/R:.4f} P(look1 o look2 estricta)={any_s/R:.4f}")
