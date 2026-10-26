"""Run de B2 fabricado para probar el control de vida: el CTL copia los resultados y grillas de S162 (vivo) o los mismos
con M14 en 0 (muerto); 60 pasadas de la muestra copian una neg_resto real de S162 del mismo volcán."""
import json, shutil, sys, random, copy
from pathlib import Path

modo = sys.argv[1]            # vivo | muerto
dest = Path(sys.argv[2])
A162 = Path("C:/vrp-trabajo/temporales/s162_v375/run_40116289866")
B2 = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))["pasadas"]
R, Z = {}, {}
for f in A162.rglob("resultados_VIIRS375_*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        R[r["id"]] = r
for z in A162.rglob("grilla_*.npz"):
    Z[int(z.stem.split("_")[1])] = z
bc = {o["id"]: o for o in json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))["pasadas"]}
negs = {}
for i, o in bc.items():
    if o["clase"] == "neg_resto" and R.get(i, {}).get("estado") == "ok":
        negs.setdefault(o["volcan"], []).append(i)
if dest.exists():
    shutil.rmtree(dest)
(dest / "s162-v375-b2-0").mkdir(parents=True)
out = []
rng = random.Random(1)
muestra = [o for o in B2 if o["lote"] == "S162b"]
for o in [x for x in B2 if x["lote"] == "CTL"] + rng.sample(muestra, 60):
    src = o["id_ref"] if o["lote"] == "CTL" else rng.choice(negs[o["volcan"]])
    r = copy.deepcopy(R[src])
    r["id"] = o["id"]
    if modo == "muerto" and o["lote"] == "CTL":
        for b in r["port"].values():
            b["npix"], b["vrp_mw"], b["pixeles"] = 0, None, []
    out.append(r)
    shutil.copy(Z[src], dest / "s162-v375-b2-0" / f"grilla_{o['id']:04d}.npz")
(dest / "s162-v375-b2-0" / "resultados_VIIRS375_00.json").write_text(json.dumps(out), encoding="utf-8")
print(modo, len(out), "pasadas fabricadas en", dest)
