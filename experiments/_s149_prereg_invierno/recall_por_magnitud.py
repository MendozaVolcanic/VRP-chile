# -*- coding: utf-8 -*-
"""S149. Recall por tramo de la magnitud que MIROVA publico. Pregunta de Nicolas: MIROVA publica bajo
0,5 MW muchas veces; el criterio de "ninguna perdida de 0,5 MW o mas" protege poco. Que pasa con las
alertas debiles? Por tramo: cuantas alertas de MIROVA hay, cuantas publica el control y cuantas el brazo.
Uso: python recall_por_magnitud.py tabla.json [tabla2.json ...]"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TRAMOS = [(0, .05), (.05, .1), (.1, .2), (.2, .5), (.5, 1e9)]
for ruta in sys.argv[1:]:
    T = json.load(open(ruta, encoding="utf-8")); print("\n== ventana", T["ventana"])
    for sensor in ("VIIRS375", "VIIRS750"):
        pos = [(v["control"], v["brazo"]) for k, v in T["pasadas"].items() if k.split("|")[1] == sensor and len(v) == 2 and v["control"]["lab"] == "pos" and v["control"]["vrp_ref"]]
        print("  %s | alertas de MIROVA con magnitud: %d" % (sensor, len(pos)))
        for a, b in TRAMOS:
            s = [(c, f) for c, f in pos if a <= c["vrp_ref"] < b]
            if not s: continue
            nc = sum(c["pub"] for c, f in s); nf = sum(f["pub"] for c, f in s)
            print("     MIROVA %-14s n %3d (%2.0f %% de las alertas) | control publica %3d (%3.0f %%) | con max %3d (%3.0f %%)" % (
                ("%.2f a %.2f MW" % (a, b)) if b < 1e8 else "0,50 MW o mas", len(s), 100 * len(s) / len(pos), nc, 100 * nc / len(s), nf, 100 * nf / len(s)))
        nc = sum(c["pub"] for c, f in pos); nf = sum(f["pub"] for c, f in pos)
        print("     TODAS                 n %3d                       | control publica %3d (%3.0f %%) | con max %3d (%3.0f %%)" % (len(pos), nc, 100 * nc / len(pos), nf, 100 * nf / len(pos)))
