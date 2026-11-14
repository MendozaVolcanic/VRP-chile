# -*- coding: utf-8 -*-
"""V5-L: 311. Prueba diferencial de las TRES copias de mirovaEqVrp con node sobre todos los records de data/mirova_equivalent (base 752d348bc).
Preg 1: si las divergencias de texto tuvieran efecto en los datos de hoy, el conteo de desacuerdos seria > 0; el control positivo inyecta 4 records sinteticos que SI
disparan cada divergencia (sin pc + far; sin pc con vrp_mir_mw; sin pc > 50000; innerKm por defecto 10 en una vista con inner 5) y exige que se vean.
Preg 2: si el extractor/evaluador estuviera muerto (funcion no encontrada) el script aborta, no da 0 desacuerdos."""
import json, os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
W = r"C:\Users\nmend\vrp-temporales\s175_audit\v5\work"
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
import yaml
Y = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
def extrae(html, nombre):
    m = re.search(r"function\s+" + nombre + r"\s*\(", html)
    assert m, nombre
    i = html.index("{", m.start()); d = 0
    for j in range(i, len(html)):
        d += html[j] == "{"; d -= html[j] == "}"
        if d == 0: return html[m.start():j + 1]
fn = {v: extrae(open(os.path.join(W, v + ".html"), encoding="utf-8").read(), "mirovaEqVrp") for v in ("index", "diario", "mosaico")}
m = re.search(r"const INNER_RADIUS_KM\s*=\s*\{.*?\};", open(os.path.join(W, "diario.html"), encoding="utf-8").read(), re.S)
assert m
inner_pre = [v for v in Y if "inner_radius_km" in Y[v]]
recs = []
for vol in inner_pre:
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p): continue
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        pc = r.get("primary_cluster")
        recs.append({"v": vol, "r": {"vrp_mw": r.get("vrp_mw"), "vrp_mir_mw": r.get("vrp_mir_mw"), "distance_class": r.get("distance_class"),
                                     "primary_cluster": ({"vrp_mw": pc.get("vrp_mw"), "centroid_dist_km": pc.get("centroid_dist_km")} if pc else None)}})
n_reales = len(recs)
sint = [("Lascar", {"vrp_mw": 0.9, "distance_class": "far", "primary_cluster": None}),
        ("Lascar", {"vrp_mw": None, "vrp_mir_mw": 0.7, "primary_cluster": None}),
        ("Lascar", {"vrp_mw": 60000, "primary_cluster": None}),
        ("Lascar", {"vrp_mw": 1, "distance_class": "summit", "primary_cluster": {"vrp_mw": 1.0, "centroid_dist_km": 7.0}})]
for v, r in sint: recs.append({"v": v, "r": r, "sint": True})
inner = {v: Y[v]["inner_radius_km"] for v in Y if "inner_radius_km" in Y[v]}
js = "\n".join([
    "const fs=require('fs');",
    "const INDEX=" + fn["index"].replace("function mirovaEqVrp", "function f") + ";",
    "const MOSAICO=" + fn["mosaico"].replace("function mirovaEqVrp", "function f") + ";",
    m.group(0), "let includeFarDistance=false;",
    "const DIARIO=" + fn["diario"].replace("function mirovaEqVrp", "function f") + ";",
    "const D=JSON.parse(fs.readFileSync(process.argv[2]));const INNER=JSON.parse(fs.readFileSync(process.argv[3]));",
    "const out=D.map(x=>[INDEX(x.r,INNER[x.v]),MOSAICO(x.r,INNER[x.v]),DIARIO(x.r,x.v),INDEX(x.r),MOSAICO(x.r)]);",
    "fs.writeFileSync(process.argv[4],JSON.stringify(out));"])
# la funcion declara con 'function f(...)' dentro de una expresion: convertir a function expression
js = js.replace("const INDEX=function f", "const INDEX=function f")
open(os.path.join(W, "dif.js"), "w", encoding="utf-8").write(js)
json.dump(recs, open(os.path.join(W, "recs.json"), "w"), ensure_ascii=False)
json.dump(inner, open(os.path.join(W, "inner.json"), "w"))
subprocess.run(["node", os.path.join(W, "dif.js"), os.path.join(W, "recs.json"), os.path.join(W, "inner.json"), os.path.join(W, "out.json")], check=True)
out = json.load(open(os.path.join(W, "out.json")))
print("records reales:", n_reales, "sinteticos:", len(recs) - n_reales)
def cuenta(cols, rango, nombre):
    dis = [i for i in rango if len({round(out[i][c], 9) for c in cols}) > 1]
    print(f"{nombre}: desacuerdos {len(dis)} de {len(list(rango))}")
    return dis
cuenta((0, 1, 2), range(n_reales), "REALES, index/mosaico con innerKm del volcan vs diario con su tabla")
cuenta((3, 4, 2), range(n_reales), "REALES, index/mosaico con innerKm POR DEFECTO (10) vs diario")
for i in range(n_reales, len(recs)):
    print("SINTETICO", i - n_reales, recs[i]["r"], "-> index,mosaico,diario(innerKm volcan) =", out[i][:3], "| index,mosaico(defecto 10) =", out[i][3:])
