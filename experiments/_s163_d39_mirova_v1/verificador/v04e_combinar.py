"""v04e_combinar.py: une los 4 fragmentos de v04d (cada uno exhaustivo en su tramo, con la version anterior como
'anterior') y responde: llaves perdidas en algun paso desde la base, cuales siguen ausentes en main (clon), en que
commit se perdieron, y cuales eran protegidas. Tambien verifica que los tramos cubren 1 + 1239 versiones sin hueco."""
import json, glob, collections, subprocess, csv, io, sys
sys.stdout.reconfigure(encoding="utf-8")
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"; RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"
frag = sorted(glob.glob("v04d_resultado_*_*.json"), key=lambda p: int(p.split("_")[2]))
pasos = []; perd = {}; prot = {}
for p in frag:
    d = json.load(open(p)); pasos += d["pasos"]
    for k, v in d["perdidas_en_algun_paso"]: perd.setdefault(tuple(k), v)
    for k, v in d["protegidas_vistas"]: prot[tuple(k)] = v
    print(p, "pasos", len(d["pasos"]), "perdidas en el tramo", len(d["perdidas_en_algun_paso"]))
print("pasos evaluados en total:", len(pasos), "(esperados 1239)")
print("pasos con perdidas:", [(s, n, pl) for s, n, r, pl, nu, ra in pasos if pl], "| con repetidas:", [(s, r) for s, n, r, pl, nu, ra in pasos if r], "| con lineas raras:", sum(1 for *_, ra in pasos if ra))
hoy = set()
for f in csv.DictReader(io.StringIO(subprocess.run(["git","-C",CLON,"show",f"main:{RUTA}"],capture_output=True,check=True).stdout.decode("utf-8"))):
    hoy.add(((f["timestamp"] or "").strip(), f["Volcan"].strip(), f["Sensor"].strip()))
aus = {k: v for k, v in perd.items() if k not in hoy}
print("llaves perdidas en algun paso:", len(perd), "| repuestas antes de hoy:", len(perd) - len(aus), "| siguen ausentes hoy:", len(aus))
print("  por commit donde se perdieron:", dict(collections.Counter(v[:10] for v in aus.values())))
pa = {k: prot[k] for k in aus if k in prot}
print("protegidas ausentes hoy:", len(pa)); [print("   ", k, v) for k, v in sorted(pa.items())]
# contra las 241 de la rama s163
rep = list(csv.DictReader(io.StringIO(subprocess.run(["git","-C",CLON,"show","s163/d39-reposicion-y-bucle:monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv"],capture_output=True,check=True).stdout.decode("utf-8"))))
kr = {((f["timestamp"] or "").strip(), f["Volcan"], f["Sensor"]) for f in rep}
print("ausentes hoy que estan en el archivo de reposicion de s163:", sum(k in kr for k in aus), "de", len(aus), "| ausentes hoy que NO estan:", [k for k in aus if k not in kr][:10])
