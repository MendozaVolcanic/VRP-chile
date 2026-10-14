# -*- coding: utf-8 -*-
"""Tarea 1.10 del loop: `max` en VIIRS 750 contra el criterio de victoria (suma de errores).

POR QUE. El criterio de Nicolas (2026-10-13; tasks/LOOP_OBJETIVOS.md §1.2) veta todo cambio que pierda una
alerta protegida (VRP de la pasada >= 1 MW, docs/S151_CRITERIO_CLASE_MIROVA.md) y, por debajo, suma alertas
perdidas y publicaciones de mas con el mismo peso. VERIFICADOR_DATOS S150 D4 encontro que `max` (brazo F)
pierde en VIIRS 750 cuatro alertas que el brazo sin Test 1 (B) publicaba: 0,65, 0,41, 0,39 y 0,32 MW.

Fuente: `pasadas_viirs750_B_F.csv` (extraer_tablas.py, desde las tablas por pasada de armar_tabla.py del A/B de
meses, control B, brazo F, referencia congelada por mes). Se cuenta pasada por pasada (version 1 contaba desde
porcentajes redondeados; el verificador limpio de la 1.10 pidio esto).

Limites que el numero NO cubre (verificador de la 1.10): (1) compara contra B, sin Test 1; produccion lo tiene
encendido; (2) las publicaciones en pasadas sin etiqueta ("sin_info", "far_ref") no entran en la suma (B 309,
F 114: favorece a F, pero no es un negativo limpio); (3) la razon de magnitud, tercera metrica del criterio,
no esta aqui; (4) con la lectura B del criterio (D-4, #782) F pierde una pasada protegida, Nevados de Chillan
2026-07-23 06:30: MIROVA vio 1,52 MW a 29,56 km (FALSO_POSITIVO del scraper) y B publico otro objeto, 0,051 MW a
4,18 km; F no publico. Con la lectura A no pierde ninguna.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

CSV = Path(__file__).resolve().parent / "pasadas_viirs750_B_F.csv"
MESES = ["abril", "mayo", "junio", "julio", "agosto"]


def main():
    c = defaultdict(lambda: defaultdict(int))
    perdidas = []
    with open(CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            m, lab, b, f = r["mes"], r["lab"], int(r["pub_B"]), int(r["pub_F"])
            if lab == "pos":
                c[m]["miss_B"] += 1 - b
                c[m]["miss_F"] += 1 - f
                c[m]["solo_F"] += int(f and not b)
                if b and not f:
                    perdidas.append((r["clave"], r["vrp_ref"]))
            elif lab == "neg_limpio":
                c[m]["neg_B"] += b
                c[m]["neg_F"] += f
    print("mes      | alertas sin publicar | negativos publicados | suma de errores | positivas que solo F publica")
    print("         | B      F             | B      F             | B      F        |")
    tot_b = tot_f = 0
    for m in MESES:
        x = c[m]
        eb, ef = x["miss_B"] + x["neg_B"], x["miss_F"] + x["neg_F"]
        tot_b += eb; tot_f += ef
        print(f"{m:8s} | {x['miss_B']:3d}  {x['miss_F']:3d}             | {x['neg_B']:3d}  {x['neg_F']:3d}             | "
              f"{eb:3d}  {ef:3d}       | {x['solo_F']}")
    print(f"total    | suma de errores B {tot_b}, F {tot_f}")
    print("positivas que B publica y F no (clave, VRP de MIROVA en MW):")
    for k, v in perdidas:
        print(f"  {k}  {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
