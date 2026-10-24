import json, collections
from pathlib import Path
R=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864")
E=R/"experiments/_s162_v375"
b2=json.loads((E/"b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))
bc=json.loads((E/"objetivos_v375_bc.json").read_text(encoding="utf-8"))
o159=[o for o in json.loads((R/"experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")) if o["b"]=="VIIRS375"]
pob=json.loads((R/"experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))
EXC=("2026-10-12","2026-10-13","2026-10-17","2026-10-18","2026-10-19","2026-10-20")
est=lambda o:f"{o['volcan']}|{o['estrato_z']}"
marco=[o for o in pob["pasadas"] if o["b"]=="VIIRS375" and o["decide"] and o["hora_utc"][:10] not in EXC and o["lab"]!="pos" and not o["pub_prod"]]
N=collections.Counter(est(o) for o in marco)
print("N neg_resto marco",sum(N.values()), "n estratos",len(N))
m=bc["meta"]["estratos"]["neg_resto"]
print("meta S162 N coincide:", all(m[h]["N"]==N[h] for h in N), sum(v["N"] for v in m.values()), "claves extra", set(m)-set(N))
n162=collections.Counter(o["estrato"] for o in bc["pasadas"] if o["clase"]=="neg_resto")
n159=collections.Counter(f"{o['volcan']}|{o['estrato_z']}" for o in o159 if o["clase"]=="neg_resto" and o["hora_utc"][:10] not in EXC)
nb=collections.Counter(o["estrato"] for o in b2["pasadas"])
print("n159",sum(n159.values()),"n162",sum(n162.values()),"nb2",sum(nb.values()))
# estrato de B2 consistente con volcan|estrato_z
print("estrato B2 consistente:", all(o["estrato"]==est(o) for o in b2["pasadas"]))
# agotamiento: disponibles
for h in sorted(N):
    disp=N[h]-n159[h]-n162[h]-nb[h]
    w=N[h]/(n162[h]+nb[h]) if n162[h]+nb[h] else None
    print(f"{h:34s} N={N[h]:4d} n159={n159[h]:3d} n162={n162[h]:3d} nb2={nb[h]:3d} resto={disp:4d} w={w:.2f}")
# suma de pesos
print("sum w deciden",sum(N[h]/(n162[h]+nb[h])*(n162[h]+nb[h]) for h in N))
# ok: 11 no observadas S162
