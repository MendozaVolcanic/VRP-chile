# Fabrica artefactos B2 de prueba a partir de pasadas neg_resto de S162 del mismo volcan (con reemplazo).
# modo: "tal" = muestreo uniforme de neg_resto ok; "caliente" = fuerza una tasa de eventos mayor (mezcla con eventos)
import json, glob, random, shutil, sys, collections
from pathlib import Path
R=Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375")
ART=Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866")
modo=sys.argv[1]; out=Path(sys.argv[2]); tasa=float(sys.argv[3]) if len(sys.argv)>3 else 0
b2=json.loads((R/"b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]
bc={o["id"]:o for o in json.loads((R/"objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]}
res={}
for f in ART.rglob("resultados_VIIRS375_*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")): res[r["id"]]=r
npz={}
for z in ART.rglob("grilla_*.npz"): npz[int(z.stem.split("_")[1])]=z
pool=collections.defaultdict(list); ev=collections.defaultdict(list)
for i,r in res.items():
    o=bc.get(i)
    if o and o["clase"]=="neg_resto" and r.get("estado")=="ok" and i in npz:
        (ev if False else pool)[o["volcan"]].append(i)
# eventos reales: leer del cache? marcamos por npix M14>0 y alertado: se identifica luego; aqui sin separar
rng=random.Random(5)
out.mkdir(parents=True,exist_ok=True)
rows=[]; mapa={}
for o in b2:
    src=rng.choice(pool[o["volcan"]])
    r=json.loads(json.dumps(res[src])); r["id"]=o["id"]; r["hora_utc"]=o["hora_utc"]; r["granule"]=o["granule"]
    rows.append(r); mapa[o["id"]]=src
    shutil.copy(npz[src], out/f"grilla_{o['id']:04d}.npz")
(out/"resultados_VIIRS375_00.json").write_text(json.dumps(rows),encoding="utf-8")
(out/"mapa.json").write_text(json.dumps(mapa),encoding="utf-8")
print("fake listo",len(rows))
