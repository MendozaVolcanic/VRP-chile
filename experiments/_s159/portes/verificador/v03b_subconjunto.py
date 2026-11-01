# -*- coding: utf-8 -*-
"""v03b: la calibración de (a) en v03 sólo discrimina donde las reglas del port difieren. Sobre alertas de la
TABLA con píxeles del port (variante sensible) donde |max_rad - cercano| > 1 km, ¿qué regla calza con MIROVA?
Pregunta 1: si todas las filas tuvieran los píxeles juntos, el subconjunto quedaría vacío y se dice SIN DATO."""
import json, sys, importlib.util
from pathlib import Path
import numpy as np
ROOT = Path(r"C:/vrp-trabajo/s159-n"); PORTES = ROOT / "experiments/_s159/portes"
ART = Path(r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(PORTES))
import banco_paridad as B
spec = importlib.util.spec_from_file_location("an04", PORTES / "04_analizar.py"); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
obj = {o["id"]: o for o in json.loads((PORTES / "objetivos_portes.json").read_text(encoding="utf-8"))}
res = {}
for f in sorted(ART.rglob("resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok": res[r["id"]] = r
for var in ("sensible", "fisica"):
    sub = []
    for i, o in sorted(obj.items()):
        if o["b"] != "VIIRS375" or o["lab"] != "pos" or i not in res: continue
        p = res[i]["port"][var]
        if not p.get("npix"): continue
        px = p["pixeles"]; d = [q[3] for q in px]; mx = px[int(np.argmax([q[4] for q in px]))][3]
        cen = A.dist_centroide(p, o["grilla"])
        for f in o["mirova"]:
            if f["source"] == "CONS" and B.es_alerta(f["tipo"]) and abs(mx - min(d)) > 1.0:
                sub.append((i, o["volcan"], o["hora_utc"], f["dist_km"], min(d), mx, round(cen, 2)))
    print(f"variante {var}: alertas de la tabla con reglas que difieren > 1 km: {len(sub)}")
    for r, k in (("cercano", 4), ("max_rad", 5), ("centroide", 6)):
        print(f"   {r}: calza (<=1 km) {sum(abs(x[3]-x[k]) <= 1 for x in sub)} de {len(sub)}")
    for x in sub: print("     ", x)
