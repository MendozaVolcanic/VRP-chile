import json, collections, sys
from pathlib import Path
R=Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/s162-viirs375-c1b864")
EXC=("2026-10-12","2026-10-13","2026-10-17","2026-10-18","2026-10-19","2026-10-20")
pob=json.load(open(R/"experiments/_s159/portes/poblacion_completa.json",encoding="utf-8"))["pasadas"]
o159=[o for o in json.load(open(R/"experiments/_s159/portes/objetivos_portes.json",encoding="utf-8")) if o["b"]=="VIIRS375"]
bc=json.load(open(R/"experiments/_s162_v375/objetivos_v375_bc.json",encoding="utf-8"))["pasadas"]
b2=json.load(open(R/"experiments/_s162_v375/b2/objetivos_v375_b2.json",encoding="utf-8"))["pasadas"]
# marco independiente: sin usar seleccion.clase
def es_negresto(o): return o["lab"]!="pos" and not o["pub_prod"]
marco=[o for o in pob if o["b"]=="VIIRS375" and o["decide"] and o["hora_utc"][:10] not in EXC and es_negresto(o)]
print("marco neg_resto", len(marco))
key=lambda o:(o["volcan"],o["hora_utc"])
mk={key(o):o for o in marco}
print("B2 en marco:", sum(key(o) in mk for o in b2), "de", len(b2))
print("B2 clave unica:", len({key(o) for o in b2}))
s159k={key(o) for o in o159}; s162k={key(o) for o in bc}
print("B2 y S159:", len({key(o) for o in b2}&s159k), "B2 y S162:", len({key(o) for o in b2}&s162k))
print("S159 neg_resto con clave en marco:", sum(key(o) in mk for o in o159), " S162 neg_resto:", sum(key(o) in mk for o in bc if o["clase"]=="neg_resto"))
# campos de B2 vs marco
dif=[o["id"] for o in b2 if any(o.get(k)!=mk[key(o)].get(k) for k in ("pub_prod","lab","protegida","mirova_vrp","z","granule","decide"))]
print("B2 con campos distintos al marco:", len(dif))
print("pub_prod en B2:", collections.Counter(o["pub_prod"] for o in b2), "lab:", collections.Counter(o["lab"] for o in b2))
print("MIROVA tipos en B2:", collections.Counter(tuple(sorted({m["tipo"] for m in o["mirova"]})) for o in b2))
print("mirova_vrp>0.05 en B2:", sum(o["mirova_vrp"]>0.05 for o in b2))
# estratos
N=collections.Counter(f"{o['volcan']}|{o['estrato_z']}" for o in marco)
nb=collections.Counter(o["estrato"] for o in b2)
tot=sum(N.values())
print("max |n_b2 - 1200*N/tot|:", max(abs(nb[h]-1200*N[h]/tot) for h in N))
print("estrato recomputado = campo:", all(o["estrato"]==f"{o['volcan']}|{o['estrato_z']}" for o in b2))
print("z<=40 coherente:", all((o["z"]<=40)==(o["estrato_z"]=="z<=40") for o in b2 if o["z"] is not None), "z None:", sum(o["z"] is None for o in b2))
# partidas
print("partidas B2:", sum(bool(o.get("partida")) for o in b2))
# noche-volcan: intra B2 y con S162, S159
def noche(o):
    h=o["hora_utc"]; d=h[:10]; hh=int(h[11:13])
    # noche local Chile ~ UTC-3/-4 : agrupar por fecha UTC-6h
    import datetime
    t=datetime.datetime.strptime(h,"%Y-%m-%d %H:%M")-datetime.timedelta(hours=6)
    return (o["volcan"],t.strftime("%Y-%m-%d"))
cn=collections.Counter(noche(o) for o in b2)
print("noches-volcan distintas en B2:", len(cn), "pasadas:", len(b2), "max pasadas por noche-volcan:", max(cn.values()))
sh=sum(1 for o in b2 if noche(o) in {noche(p) for p in bc if p["clase"]=="neg_resto"}|{noche(p) for p in o159})
print("pasadas B2 cuya noche-volcan tambien tiene una pasada de S159/S162 neg_resto:", sh)
# volcán
print(collections.Counter(o["volcan"] for o in b2))
print("S162 neg_resto por volcan", collections.Counter(o["volcan"] for o in bc if o["clase"]=="neg_resto"))
print("marco por volcan", collections.Counter(o["volcan"] for o in marco))
print("fechas B2 excluidas:", sum(o["hora_utc"][:10] in EXC for o in b2), " rango", min(o["hora_utc"] for o in b2), max(o["hora_utc"] for o in b2))
