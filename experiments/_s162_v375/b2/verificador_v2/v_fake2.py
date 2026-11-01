# Fabrica artefactos B2 de prueba (SOLO para probar el cableado): para cada id de B2 copia el resultado y la grilla de una
# pasada neg_resto real de S162 del mismo volcan. Modos: ids a omitir (para probar cobertura), semilla.
import json, random, shutil, sys, collections
from pathlib import Path
R=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375")
ART=Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866")
out=Path(sys.argv[1]); semilla=int(sys.argv[2]); omitir=int(sys.argv[3])  # omitir: cuantas pasadas B2 sin resultado
b2=json.loads((R/"b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]
bc={o["id"]:o for o in json.loads((R/"objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]}
res={}
for f in ART.rglob("resultados_VIIRS375_*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")): res[r["id"]]=r
npz={}
for z in ART.rglob("grilla_*.npz"): npz[int(z.stem.split("_")[1])]=z
pool=collections.defaultdict(list)
for i,r in res.items():
    o=bc.get(i)
    if o and o["clase"]=="neg_resto" and r.get("estado")=="ok" and i in npz: pool[o["volcan"]].append(i)
rng=random.Random(semilla); out.mkdir(parents=True,exist_ok=True)
rows=[]; mapa={}
om=set(rng.sample([o["id"] for o in b2], omitir)) if omitir else set()
for o in b2:
    if o["id"] in om: continue
    src=rng.choice(pool[o["volcan"]])
    r=json.loads(json.dumps(res[src])); r["id"]=o["id"]; r["hora_utc"]=o["hora_utc"]; r["granule"]=o["granule"]
    rows.append(r); mapa[o["id"]]=src
    shutil.copy(npz[src], out/f"grilla_{o['id']:04d}.npz")
(out/"resultados_VIIRS375_00.json").write_text(json.dumps(rows),encoding="utf-8")
(out/"mapa.json").write_text(json.dumps({"mapa":mapa,"omitidas":sorted(om)}),encoding="utf-8")
print("fake listo",len(rows),"omitidas",len(om))
