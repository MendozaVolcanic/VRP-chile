import json,math,collections,sys
sys.path.insert(0,'.')
from recuento import *
meta=o162['meta']['estratos']
print({c:sum(v['N'] for v in e.values()) for c,e in meta.items()})
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(max(p*(1-p)/n+z*z/(4*n*n),0))/d
    return max(0,c-h),min(1,c+h)
def kish(w): return sum(w)**2/sum(x*x for x in w)
def tasa(rows):  # rows: (w, pub)
    w=[r[0] for r in rows]; p=sum(r[0]*r[1] for r in rows)/sum(w); ne=kish(w)
    return p,wilson(p*ne,ne),ne
# neg_resto B2
cnt=collections.Counter(); 
rowsB=[]
ok=[i for i,r in b2.items() if r['estado']=='ok' and OB[i]['lote']=='S162b']
for i in ok: cnt[OB[i]['estrato']]+=1
NB=meta['neg_resto']
# N por estrato: meta neg_resto de o162 (marco) vs b2 meta
Nb2={h:v['N'] for h,v in ob['meta']['estratos_neg_resto'].items()}
print("N neg_resto marco (o162 meta)",sum(v['N'] for v in NB.values()),"N b2 meta",sum(Nb2.values()))
print("coinciden N?",all(NB[h]['N']==Nb2[h] for h in NB))
for i in ok:
    h=OB[i]['estrato']; rowsB.append((NB[h]['N']/cnt[h], 1 if pub(b2[i])[0] else 0))
pB,icB,neB=tasa(rowsB); print("neg_resto B2: pond",pB,"IC",icB,"neff",neB,"crudo",sum(r[1] for r in rowsB),len(rowsB))
# neg_pub S162
cntp=collections.Counter(); 
okp=[i for i,r in s162.items() if r['estado']=='ok' and O162[i]['lote']=='S162' and O162[i]['clase']=='neg_pub']
for i in okp: cntp[O162[i]['estrato']]+=1
NP=meta['neg_pub']
rowsP=[(NP[O162[i]['estrato']]['N']/cntp[O162[i]['estrato']], 1 if pub(s162[i])[0] else 0) for i in okp]
pP,icP,neP=tasa(rowsP); print("neg_pub S162: pond",pP,"IC",icP,"neff",neP,"crudo",sum(r[1] for r in rowsP),len(rowsP), "sum N",sum(v['N'] for v in NP.values()))
Np=sum(v['N'] for v in NP.values()); Nr=sum(v['N'] for v in NB.values()); tot=Np+Nr
pn=(Np*pP+Nr*pB)/tot; lo=(Np*icP[0]+Nr*icB[0])/tot; hi=(Np*icP[1]+Nr*icB[1])/tot
print("Np,Nr",Np,Nr,"K",Np/tot,"pn",pn,"IC",lo,hi)
# sensibilidad: cuantas de las 35 hacen falta para cruzar
for extra in range(0,40,5):
    k=6+extra; n=1200
    print(extra, "crudo neg_resto",k/n)
# cota en peor caso: las 35 publican con tasa p
import itertools
def hi_con(extra):
    rows=[]
    # asignar extras a los estratos de los fuera
    fu=[i for i,r in b2.items() if r['estado']!='ok' and i<5000]
    cn=collections.Counter(OB[i]['estrato'] for i in ok)|collections.Counter()
    return None
