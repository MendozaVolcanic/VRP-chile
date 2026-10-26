# -*- coding: utf-8 -*-
"""03d: donde caen los cumulos que publicamos en negativos limpios de Cordon Caulle (MIROVA miro y no vio nada), por sensor,
con su posicion respecto del vent y del anillo de MIROVA (desde el centro del TIF). Corrido en la sesion como heredoc
(salida en 03d_negativos_pcc_salida.txt).
Uso: PYTHONIOENCODING=utf-8 python 03d_negativos_pcc.py > 03d_negativos_pcc_salida.txt
"""
import collections
import csv

import comun as C

pas = list(csv.DictReader(open('03_pareo_geometria_pasadas.csv', encoding='utf-8')))
g = C.GEO['PuyehueCordonCaulle']
tc = g['tif_centro']
for b in ('VIIRS375', 'VIIRS750', 'MODIS'):
    sel = [r for r in pas if r['vol'] == 'PuyehueCordonCaulle' and r['b'] == b and r['lab'] == 'neg_limpio' and r['pub'] == '1']
    print(f"\n== PCC {b}: {len(sel)} negativos limpios publicados")
    bins = collections.Counter()
    for r in sel:
        la, lo = float(r['pc_lat']), float(r['pc_lon'])
        de, dn = C.dxy_km(tc[0], tc[1], la, lo)
        en_anillo = abs(dn) <= C.ANILLO_KM and abs(de) <= 9.5 * 0.75
        bins[(round(la / 0.04) * 0.04, round(lo / 0.04) * 0.04)] += 1
        print(f"   {r['hora']} pc {r['pc_vrp']} MW n={r['pc_n']} a {float(r['pc_dvent']):5.2f} km {C.octante(float(r['pc_rvent']))} del vent; "
              f"centro TIF dN {dn:+5.1f} dE {de:+5.1f} (anillo {en_anillo}); t_max {r['t_max']} z {r['z']} fhs={r['fhs']} regimen={r['regimen']}")
    print("   celdas 0,04 grados mas repetidas:", bins.most_common(5))
