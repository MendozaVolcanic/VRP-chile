import json, collections, hashlib, sys, datetime as dt
from pathlib import Path
R=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864")
b2=json.loads((R/"experiments/_s162_v375/b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))
bc=json.loads((R/"experiments/_s162_v375/objetivos_v375_bc.json").read_text(encoding="utf-8"))
o159=[o for o in json.loads((R/"experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")) if o["b"]=="VIIRS375"]
pob=json.loads((R/"experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))
print("sha pob", hashlib.sha256((R/"experiments/_s159/portes/poblacion_completa.json").read_bytes()).hexdigest()[:12])
B=b2["pasadas"]; print("B2 n",len(B), collections.Counter(o["clase"] for o in B), collections.Counter(o["lote"] for o in B))
k=lambda o:(o["volcan"],o["hora_utc"])
seen=set(k(o) for o in o159)|set(k(o) for o in bc["pasadas"])
print("interseccion exacta con S159/S162 (todas clases):", len({k(o) for o in B}&seen), "dup interno", len(B)-len({k(o) for o in B}))
# marco desde poblacion
EXC=("2026-10-12","2026-10-13","2026-10-17","2026-10-18","2026-10-19","2026-10-20")
P={k(o):o for o in pob["pasadas"] if o["b"]=="VIIRS375"}
bad=0; ctr=collections.Counter()
for o in B:
    p=P.get(k(o))
    if p is None: bad+=1; continue
    ctr[(p["decide"], p["lab"], p["pub_prod"], p["protegida"] if "protegida" in p else None, p["hora_utc"][:10] in EXC)]+=1
print("no esta en poblacion:",bad); print(ctr)
# IDs
ids=[o["id"] for o in B]; print("ids",min(ids),max(ids), len(set(ids)))
allids=set(o["id"] for o in bc["pasadas"])|set(o["id"] for o in o159)
print("ids chocan:", len(set(ids)&allids))
# same volcano same night / within 10 min as S162 or S159 neg_resto
def t(o): return dt.datetime.strptime(o["hora_utc"][:16],"%Y-%m-%d %H:%M")
prev=[o for o in bc["pasadas"] if o["clase"]=="neg_resto"]+[o for o in o159 if o["clase"]=="neg_resto"]
idx=collections.defaultdict(list)
for o in prev: idx[o["volcan"]].append(t(o))
c10=c1d=0
for o in B:
    d=min([abs((t(o)-x).total_seconds()) for x in idx[o["volcan"]]] or [1e9])
    if d<=600: c10+=1
    if d<=86400: c1d+=1
print("B2 con previa neg_resto mismo volcan <=10min:",c10," <=24h:",c1d)
# comparar con esperado aleatorio: dentro de B2 y dentro de S162
