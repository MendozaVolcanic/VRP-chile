import json,sys,math,collections
import numpy as np
SP=sys.argv[1]
R=r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375"
mapa=json.load(open(SP+"/mapa.json"))["mapa"]
b2={o["id"]:o for o in json.load(open(R+"/b2/objetivos_v375_b2.json",encoding="utf-8"))["pasadas"]}
bcj=json.load(open(R+"/objetivos_v375_bc.json",encoding="utf-8"))
ev={1562,1704,1189,1473}
# N de estrato
N=collections.Counter(); 
meta=json.load(open(R+"/b2/objetivos_v375_b2.json",encoding="utf-8"))["meta"]["estratos_neg_resto"]
n=collections.Counter(); k=collections.Counter()
for i,s in mapa.items():
    h=b2[int(i)]["estrato"]; n[h]+=1; k[h]+= (s in ev)
w={h:meta[h]["N"]/n[h] for h in n}
W=np.array([w[b2[int(i)]["estrato"]] for i in mapa]); K=np.array([mapa[i] in ev for i in mapa],float)
p=(W*K).sum()/W.sum(); ne=W.sum()**2/(W**2).sum()
def wil(p,n,z=1.96):
    d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
print("eventos",int(K.sum()),"de",len(K),"pond",p,"neff",ne,"IC",wil(p,ne))
