import json, sys, collections, math
import numpy as np
E=r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375"
SC=sys.argv[1]
bc=json.load(open(E+r"\objetivos_v375_bc.json",encoding="utf-8")); b2=json.load(open(E+r"\b2\objetivos_v375_b2.json",encoding="utf-8"))["pasadas"]
mapa={int(k):v for k,v in json.load(open(SC+"/fake1/mapa.json")).items()}
ev={1562,1189,1473,1704}
N={h:v["N"] for h,v in bc["meta"]["estratos"]["neg_resto"].items()}
fuera={1019,1184,1192,1232,1318,1403,1485,1556,1601,1611,1673}
k=collections.Counter(); n=collections.Counter()
for o in bc["pasadas"]:
    if o["clase"]=="neg_resto" and o["id"] not in fuera:
        n[o["estrato"]]+=1; k[o["estrato"]]+= o["id"] in ev
for o in b2:
    n[o["estrato"]]+=1; k[o["estrato"]]+= mapa[o["id"]] in ev
def wil(x,m,z):
    p=x/m; d=1+z*z/m; c=(p+z*z/(2*m))/d; h=z*math.sqrt(max(p*(1-p)/m+z*z/(4*m*m),0))/d; return c-h,c+h
rows=np.concatenate([[N[h]/n[h]]*n[h] for h in N]); ne=rows.sum()**2/(rows**2).sum()
p=sum(N[h]*k[h]/n[h] for h in N)/sum(N.values())
print("k",sum(k.values()),"n",sum(n.values()),"p",p,"ne",ne, wil(p*ne,ne,1.96), wil(p*ne,ne,2.241))
