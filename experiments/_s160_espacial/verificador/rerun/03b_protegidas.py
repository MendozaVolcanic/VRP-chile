# -*- coding: utf-8 -*-
"""03b: lista de las protegidas (lectura A, >= 1 MW) pareadas con record nuestro en los 3 volcanes, con nuestro resultado.
Instrumento: 03_pareo_geometria_pasadas.csv. Corrido en la sesion como heredoc (salida en 03b_protegidas_salida.txt).
Uso: PYTHONIOENCODING=utf-8 python 03b_protegidas.py > 03b_protegidas_salida.txt
"""
import csv

import comun as C

pas = list(csv.DictReader(open('03_pareo_geometria_pasadas.csv', encoding='utf-8')))
print("protegidas (lectura A, >= 1 MW) pareadas con record nuestro, 3 volcanes, todas las fuentes:")
for r in pas:
    if r['lab'] == 'pos' and r['protegida'] == 'True':
        oct_ = C.octante(float(r['pc_rvent'])) if r['pc_rvent'] else None
        print(f"{r['vol']:20s} {r['b']:8s} {r['hora']} MIROVA {r['mir_vrp']} MW @{r['mir_dist']} km [{r['mir_src']}] tramo {r['tramo']:14s} "
              f"-> {r['clase']:34s} dc={r['dc']} pc={r['pc_vrp']} MW d_vent={r['pc_dvent']} oct={oct_} z={r['z']} t_max={r['t_max']}")
