# -*- coding: utf-8 -*-
"""VP162 verificador, v05: ¿publica el tablero los 6 records de K re-corrido? Predicado ejecutado con node desde
frontend/index.html (banco_paridad.correr_node, A97), no reconstruido. Pregunta 2 (instrumento vivo): control de
identidad de banco_paridad (5 casos S139 + publica/no publica) tiene que dar el patron esperado.
Variante: el mismo record con el cumulo primario movido a 9 km (far) tiene que dejar de publicar (control negativo).
"""
import io, json, glob, sys, copy
from pathlib import Path
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R/"scripts")); sys.path.insert(0, str(R))
import banco_paridad as B
print("HTML:", B.HTML)
print("control identidad:", B.control_identidad_predicado(), "(esperado ([0,1,0,1,0],[1,0]) o equivalente del guard)")
ART = r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945"
rs = {r["id"]: r for f in sorted(glob.glob(ART + r"\s159-portes-VIIRS375-*\resultados_VIIRS375_*.json"))
      for r in json.load(open(f, encoding="utf-8"))}
V = {v["name"]: v for v in yaml.safe_load(open(R/"volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
casos, et = [], []
for i in (279, 285, 288, 289, 294, 295):
    k = copy.deepcopy(rs[i]["K"]["record"]); k.setdefault("anomaly_pixels", [])
    inner = V[rs[i]["volcan"]]["inner_radius_km"]
    casos.append([{c: k.get(c) for c in B.CAMPOS_JS}, inner]); et.append(f"{i} K")
    neg = copy.deepcopy(k); neg["distance_class"] = "far"; neg["primary_cluster"]["centroid_dist_km"] = 9.0
    casos.append([{c: neg.get(c) for c in B.CAMPOS_JS}, inner]); et.append(f"{i} K movido a far 9 km")
for e, (c, inner), res in zip(et, casos, B.correr_node(casos)):
    print(f"  {e:24s} inner {inner} dc {c['distance_class']:6s} pc {c['primary_cluster']['vrp_mw']} -> [summit, valid, artefacto, display_MW, PUBLICA] = {res}")
