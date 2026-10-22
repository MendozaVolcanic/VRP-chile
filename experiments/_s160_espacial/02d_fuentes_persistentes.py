# -*- coding: utf-8 -*-
"""02d: fuentes persistentes en los TIF (VIIRS 375): celdas (0,02 grados ~2 km) donde cae el foco del residuo repetidamente,
por etiqueta de MIROVA, con su prominencia. Instrumento: 02b_tif_v375_focos.csv. Corrido en la sesion como heredoc
(salida en 02d_fuentes_persistentes_salida.txt). P1: Lascar debe dar como celda dominante la del crater; P2: n por celda.
Uso: PYTHONIOENCODING=utf-8 python 02d_fuentes_persistentes.py > 02d_fuentes_persistentes_salida.txt
"""
import collections
import csv

import comun as C

F = list(csv.DictReader(open('02b_tif_v375_focos.csv', encoding='utf-8')))
for v in C.VOLS + ['Lascar']:
    g = C.GEO.get(v) or {"vent": (-23.36293, -67.731416)}
    fv = [r for r in F if r['vol'] == v]
    print(f"\n== {v}: {len(fv)} TIF; celdas (0,02 x 0,02 grados ~2 km) mas repetidas del foco, por etiqueta:")
    for lab in ('ALERTA', 'FALSO', 'RUTINA', ''):
        sel = [r for r in fv if (r['mir_tipo'].startswith(lab) if lab else r['mir_tipo'] == '')]
        c = collections.Counter((round(float(r['lat']) / 0.02) * 0.02, round(float(r['lon']) / 0.02) * 0.02) for r in sel)
        desc = []
        for (la, lo), n in c.most_common(4):
            d = C.hav_km(la, lo, *g['vent'])
            b = C.octante(C.rumbo_deg(g['vent'][0], g['vent'][1], la, lo))
            prom = [float(r['res_sigma']) for r in sel
                    if round(float(r['lat']) / 0.02) * 0.02 == la and round(float(r['lon']) / 0.02) * 0.02 == lo]
            desc.append(f"({la:.2f},{lo:.2f}) n={n} a {d:.1f} km {b} del vent, prom p50 {sorted(prom)[len(prom)//2]:.1f}")
        print(f"  {lab or 'sin fila':8s} n={len(sel):3d}: " + " | ".join(desc))
