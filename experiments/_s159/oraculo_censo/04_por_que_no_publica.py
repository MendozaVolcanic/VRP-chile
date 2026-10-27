# -*- coding: utf-8 -*-
"""S159, censo del oráculo, paso 4 (descriptivo, post hoc): de los negativos limpios con píxeles del oráculo que el
predicado del tablero no publica, por qué (distance_class far por el inner del tablero, VRP <= 0 o artefacto cirrus).
Pregunta 1: si el contador estuviera roto daría 0 en todo; la suma tiene que dar los 28 (O-sens) y 2 (O-def) de 03.
Uso: python 04_por_que_no_publica.py --art <carpeta del censo>
"""
import argparse, collections, glob, importlib.util, json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
R = AQUI.parents[2]
sys.path.insert(0, str(R / "scripts")); sys.path.insert(0, str(R / "experiments/_s158_audit_r2/oraculo"))
spec = importlib.util.spec_from_file_location("cen", R / "experiments/_s159/n/07_censo_analizar.py")
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
import banco_paridad as B
ap = argparse.ArgumentParser(); ap.add_argument("--art", required=True); a = ap.parse_args()
inner = B.inner_desde_html()
obj = {e["id"]: e for e in json.load(open(AQUI / "objetivos.json", encoding="utf-8"))}
for caja in ("geo_linear", "geo_linear_anillo_sensible"):
    c = collections.Counter(); far = []
    for f in sorted(Path(a.art).rglob("resultados_*.json")):
        for r in json.load(open(f)):
            if r.get("estado") != "ok" or obj[r["id"]]["lab"] != "neg_limpio":
                continue
            o = r["oraculo"][caja]
            if not o.get("npix"):
                continue
            rec = C.record_oraculo(o, inner[r["volcan"]], obj[r["id"]]["sensor"])
            k = (rec["distance_class"], rec["vrp_mw"] > 0, rec["t_max_k"] < 273.15 and rec["vrp_mw"] > 10)
            c[k] += 1
            if k[0] == "far":
                far.append((r["volcan"], r["hora_utc"], rec["primary_cluster"]["centroid_dist_km"], inner[r["volcan"]], rec["vrp_mw"]))
    print(caja, "(distance_class, vrp>0, cirrus):", dict(c))
    print("   far:", sorted(far))
