# -*- coding: utf-8 -*-
"""VB2: potencia del control «B0 y B1 = censo S159» de analizar_v750b.py.

Preguntas del instrumento. (1) Si el oráculo del run estuviera roto (distinto del censo), ¿el control lo vería? Se cuenta
en cuántas de las pasadas comparadas el censo tiene al menos un píxel alertado (si casi todas dan 0 píxeles, «igual»
sería casi trivial) y se muta UN resultado de B0 en una pasada con píxeles y OTRO en una pasada sin píxeles. (2) Si el
instrumento estuviera muerto (sin pasadas comunes), el control cae a FALLA (bool(cnt) falso), no a OK: se verifica con un
censo vacío. Control positivo: las dos mutaciones tienen que dar DISTINTO.
Uso: python potencia_control_censo.py --arbol <arbol> --ens <carpeta del ensayo> --censo-art <...> --censo-obj <...> --dest <tmp>
"""
import argparse, json, subprocess, sys, shutil, collections
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument("--arbol", required=True); ap.add_argument("--ens", required=True)
ap.add_argument("--censo-art", required=True); ap.add_argument("--censo-obj", required=True)
ap.add_argument("--dest", required=True)
a = ap.parse_args()
A, ens, dest = Path(a.arbol).resolve(), Path(a.ens).resolve(), Path(a.dest).resolve()
dest.mkdir(parents=True, exist_ok=True)
res = json.loads((ens / "art" / "resultados_00.json").read_text(encoding="utf-8"))
obj = {o["id"]: o for o in json.loads((ens / "objetivos_ensayo.json").read_text(encoding="utf-8"))}
cobj = {(o["volcan"], o["hora_utc"]): o["id"] for o in json.loads(Path(a.censo_obj).read_text(encoding="utf-8"))}
cres = {}
for f in sorted(Path(a.censo_art).rglob("resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in cres:
            cres[r["id"]] = r
cnt = collections.Counter()
con_px, sin_px = [], []
for r in res:
    j = cobj.get((obj[r["id"]]["volcan"], obj[r["id"]]["hora_utc"]))
    rc = cres.get(j)
    if not rc or rc.get("estado") != "ok":
        continue
    for c, ref in (("B0", "geo_linear"), ("B1", "geo_linear_anillo_sensible")):
        y = (rc.get("oraculo") or {}).get(ref) or {}
        cnt[(c, "comparadas")] += 1
        if (y.get("npix") or 0) > 0:
            cnt[(c, "con_pixeles_en_el_censo")] += 1
            if c == "B0":
                con_px.append(r["id"])
        elif c == "B0":
            sin_px.append(r["id"])
print("potencia:", dict(cnt))


def correr(nombre, res_mut):
    d = dest / nombre
    (d / "art").mkdir(parents=True, exist_ok=True)
    (d / "art" / "resultados_00.json").write_text(json.dumps(res_mut), encoding="utf-8")
    o = subprocess.run([sys.executable, str(A / "experiments/_s162_v750b/analizar_v750b.py"), "--art", str(d / "art"),
                        "--objetivos", str(ens / "objetivos_ensayo.json"), "--evaluador",
                        str(A / "experiments/_s157_prereg_d25/evaluar_d25.py"), "--solo-controles",
                        "--censo-art", a.censo_art, "--censo-objetivos", a.censo_obj, "--salida", str(d / "s.txt")],
                       capture_output=True, text=True, cwd=str(A), encoding="utf-8", errors="replace")
    l = [x for x in o.stdout.splitlines() if "censo S159" in x or "compuerta" in x]
    print(nombre, "->", " | ".join(l))


import copy
m1 = copy.deepcopy(res)
x = next(r for r in m1 if r["id"] == con_px[0])
x["oraculo"]["B0"]["vrp_mw"] = (x["oraculo"]["B0"]["vrp_mw"] or 0) + 1e-4     # un píxel con VRP distinto en 1e-4
m2 = copy.deepcopy(res)
x = next(r for r in m2 if r["id"] == sin_px[0])
x["oraculo"]["B1"]["npix"] = 1                                                   # un píxel de más donde el censo no tiene
m3 = copy.deepcopy(res)
x = next(r for r in m3 if r["id"] == con_px[0])
x["oraculo"]["B0"]["pixeles"] = [[0, 0, 2, 0.0, 0.0]] * len(x["oraculo"]["B0"]["pixeles"])   # mismos npix y VRP, otra POSICIÓN
correr("sin_mutar", res)
correr("mut_vrp_1e-4", m1)
correr("mut_npix_en_pasada_vacia", m2)
correr("mut_posicion_misma_cuenta_y_vrp", m3)
