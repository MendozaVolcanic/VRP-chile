# VE2: la premisa "lo correcto es no publicar" en far_tabla: la Distancia_km de la fila FALSO_POSITIVO de MIROVA contra el
# inner_radius_km del tablero. Si MIROVA ubica el foco a <= inner, para NUESTRA frontera esa fuente es de cumbre y publicar es correcto.
# P1: ve el defecto si hay far_tabla con dist_ref <= inner (control positivo: cuenta cuantas). P2: instrumento muerto => n=0 sin dist_ref; se declara.
import json, collections, sys
from pathlib import Path
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
sys.path.insert(0, str(R/"scripts")); sys.path.insert(0, str(R))
import banco_paridad as B
ih = B.inner_desde_html()
d = json.load(open(R/"experiments/_s162_v375/e_adenda2/objetivos_far_v375.json", encoding="utf-8"))["pasadas"]
ft = [o for o in d if o["clase"] == "far_tabla"]
print("far_tabla", len(ft), "con dist_ref", sum(o["dist_ref"] is not None for o in ft))
ca = collections.Counter(); tot = collections.Counter(); pubK = collections.Counter()
for o in ft:
    i = ih[o["volcan"]]; dr = o["dist_ref"]
    tot[o["volcan"]] += 1
    if dr is not None and dr <= i:
        ca[o["volcan"]] += 1
        pubK[o["volcan"]] += bool(o["pub_prod"])
print("far_tabla con dist_ref <= inner del tablero (por volcan):", dict(ca), "total", sum(ca.values()))
print("  de ellas K publica:", dict(pubK), sum(pubK.values()))
# mas filas: cualquier fila FP de la tabla de la pasada con dist <= inner
alg = 0; lst = []
for o in ft:
    i = ih[o["volcan"]]
    fp = [f for f in o["mirova"] if str(f.get("tipo","")).startswith("FALSO_POSITIVO") and f.get("source")=="CONS" and f.get("dist_km") is not None]
    if any(f["dist_km"] <= i for f in fp): alg += 1; lst.append((o["volcan"], o["hora_utc"], [f["dist_km"] for f in fp], i))
print("far_tabla con ALGUNA fila FP de la tabla <= inner:", alg, lst[:15])
# multiples filas FP con distancias distintas
mult = [(o["volcan"], o["hora_utc"], sorted({f["dist_km"] for f in o["mirova"] if str(f.get("tipo","")).startswith("FALSO_POSITIVO") and f.get("dist_km") is not None})) for o in ft]
print("pasadas con >1 distancia FP distinta:", sum(1 for m in mult if len(m[2]) > 1), [m for m in mult if len(m[2])>1][:5])
# ratio dist/inner
print("PCC (inner 20) far_tabla:", [(o["hora_utc"], o["dist_ref"], bool(o["pub_prod"])) for o in ft if o["volcan"]=="PuyehueCordonCaulle"])
# control de la distribucion de dist_ref por volcan
for v in sorted(tot):
    ds = sorted(o["dist_ref"] for o in ft if o["volcan"]==v and o["dist_ref"] is not None)
    print(f"  {v:20s} n={tot[v]:3d} inner={ih[v]:>4} dist_ref min={ds[0] if ds else None} med={ds[len(ds)//2] if ds else None}")
