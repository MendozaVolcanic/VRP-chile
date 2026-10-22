# -*- coding: utf-8 -*-
"""VA, hallazgo 8 y su cruce con el 2: records VIIRS 750 que existen solo por el segundo pase, y si son los que
publican 0,0 MW en la cumbre.

Camino propio: diag_n_first_pass_pixels y diag_n_second_pass_recapture leidos directo de data/mirova_equivalent.
Pregunta 1: si el segundo pase no agregara nada, diag_n_second_pass_recapture seria 0 en todos; control positivo:
records con first_pass > 0 deben existir y mayoritariamente publicar > 0.
Pregunta 2: si los diag no existieran en el record (nombre cambiado), el conteo de campos presentes lo dice.
Ademas: un pixel publicado con bt_k <= t_bg_k + 3 no pudo salir del primer pase (compuerta bt > t_bg + 3 K,
detection_context.py:546) mientras los demas caminos esten apagados (n_bt_path = n_nti_path = 0).
Ventana: todo el corpus V750.
"""
import glob, json, sys
from collections import Counter
import yaml

sys.stdout.reconfigure(encoding="utf-8")
inner = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
c = Counter()
fe = []
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    vol = d["volcano"]
    for r in d["records"]:
        if not r.get("sensor", "").endswith("_750"):
            continue
        c["V750 total"] += 1
        if "diag_n_first_pass_pixels" not in r:
            c["sin campo diag_n_first_pass_pixels"] += 1
            continue
        fp = r.get("diag_n_first_pass_pixels") or 0
        sp = r.get("diag_n_second_pass_recapture") or 0
        n = r.get("n_anomalous_pixels") or 0
        if n == 0:
            continue
        c["con pixeles anomalos"] += 1
        fe.append(r["datetime_utc"])
        otros = (r.get("n_bt_path") or 0) + (r.get("n_nti_path") or 0) + (r.get("n_test1_pixels") or 0)
        if otros:
            c["con otros caminos > 0"] += 1
        solo2 = fp == 0 and sp > 0
        c["solo segundo pase" if solo2 else ("primer pase > 0" if fp > 0 else "fp=0 y sp=0 (otro camino)")] += 1
        pc = r.get("primary_cluster")
        cumbre = pc and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= inner[vol]
        if cumbre:
            cero = (pc.get("vrp_mw") or 0) == 0
            c[("cumbre", "solo2" if solo2 else "fp>0", "cero" if cero else ">0")] += 1
        # pixeles publicados que no pueden venir del primer pase
        aps = r.get("anomaly_pixels") or []
        if fp > 0 and aps:
            frios = sum(1 for a in aps if a["bt_k"] <= r["t_bg_k"] + 3.0)
            if frios:
                c["records fp>0 con algun pixel listado bt<=t_bg+3 (recapturado por el 2.o pase)"] += 1
print("ventana obs (con pixeles):", min(fe), "a", max(fe))
for k, v in sorted(c.items(), key=lambda x: str(x[0])):
    print(k, v)
