import numpy as np, math, json
from scipy import stats
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(max(p*(1-p)/n+z*z/(4*n*n),0))/d
    return c-h,c+h
NP,NR=133,3323; VARA=NP/(NP+NR); PUBHI=0.3652
lim=(VARA*(NP+NR)-NP*PUBHI)/NR
print("limite neg_resto", lim)
for n in (1200,1000,1500):
    kmax=max(k for k in range(0,200) if wilson(k,n)[1]<lim)
    print(n,"eventos maximos que aun deciden:",kmax,"(",kmax/n,")")
n=1200; kmax=max(k for k in range(0,200) if wilson(k,n)[1]<lim)
# potencia puntual y predictiva (posterior Beta de S162: 4 de 389, prior Jeffreys y prior plano)
def pot(p): return stats.binom.cdf(kmax,n,p)
for p in (0.0116,0.0103,0.014,0.017,0.02,0.0254): print("p",p,"potencia exacta",round(pot(p),3))
for nombre,(a,b) in {"Jeffreys":(4.5,385.5),"plano":(5,386)}.items():
    # beta-binomial predictiva
    pred=stats.betabinom.cdf(kmax,n,a,b)
    print("predictiva",nombre,round(pred,3))
# error en la frontera: tasa=lim en neg_resto => P(declarar ACOTADO) si neg_pub verdadero justo en su cota
print("tamano en frontera p=lim:",round(pot(lim),4))
# lo que declara ACOTADO cuando el total verdadero = vara y neg_pub verdadero = x (usando neg_pub fija en su cota)
for x in (0.2,0.27,0.3652,0.4):
    # total = (NP*x + NR*p)/(NP+NR)=VARA -> p
    p=(VARA*(NP+NR)-NP*x)/NR
    print("neg_pub verdadero",x,"=> neg_resto frontera",round(p,4),"P(ACOTADO)",round(pot(p),4))
