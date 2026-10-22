# -*- coding: utf-8 -*-
"""03c: nuestros cumulos PUBLICADOS (negativos limpios, alertas, far_ref, sin_info) a <= 2 km de las celdas persistentes que
02d encontro en los TIF, y si esas celdas caen en la caja / el anillo de MIROVA (desde el centro del TIF) o en nuestro inner.
Corrido en la sesion como heredoc (salida en 03c_negativos_cerca_de_fuentes_salida.txt).
Uso: PYTHONIOENCODING=utf-8 python 03c_negativos_cerca_de_fuentes.py > 03c_negativos_cerca_de_fuentes_salida.txt
"""
import csv

import comun as C

FUENTES = {
    'PuyehueCordonCaulle': [(-40.52, -72.02, '10,7 km E del vent (RUTINA 15/161, prom 10 sigma)'), (-40.52, -72.14, 'vent 2011 / lacolito')],
    'Isluga': [(-19.10, -68.84, '5,7 km N del vent (ALERTA 8, RUTINA 7, prom 4,5)'), (-19.16, -68.84, '1,5 km SW (crater activo)')],
    'Tupungatito': [(-33.34, -69.84, '5,6 km N del vent (RUTINA 13, prom 4,1)'), (-33.48, -69.74, '12,9 km SE'), (-33.38, -69.82, 'crater')],
}
pas = list(csv.DictReader(open('03_pareo_geometria_pasadas.csv', encoding='utf-8')))
for v, fs in FUENTES.items():
    g = C.GEO[v]
    tc = g['tif_centro']
    print(f"\n== {v}")
    for la, lo, desc in fs:
        de, dn = C.dxy_km(tc[0], tc[1], la, lo)
        en_anillo = abs(dn) <= C.ANILLO_KM and abs(de) <= 9.5 * 0.75
        en_caja = abs(dn) <= C.CAJA_KM and abs(de) <= C.CAJA_KM
        d_tc = C.hav_km(la, lo, *tc)
        d_v = C.hav_km(la, lo, *g['vent'])
        print(f"  fuente ({la},{lo}) {desc}: a {d_tc:.1f} km del centro TIF (dN {dn:+.1f}, dE {de:+.1f}), {d_v:.1f} km del vent; "
              f"en caja {en_caja}, en anillo {en_anillo}, dentro de inner {d_v <= g['inner_km']}")
        for b in ('VIIRS375', 'VIIRS750', 'MODIS'):
            for lab in ('neg_limpio', 'pos', 'far_ref', 'sin_info'):
                sel = [r for r in pas if r['vol'] == v and r['b'] == b and r['lab'] == lab and r['pub'] == '1' and r['pc_lat']]
                cerca = [r for r in sel if C.hav_km(float(r['pc_lat']), float(r['pc_lon']), la, lo) <= 2.0]
                if sel and (lab in ('neg_limpio', 'pos') or cerca):
                    print(f"     {b:8s} {lab:10s} publicados {len(sel):4d}, con cumulo a <= 2 km de la fuente: {len(cerca)}"
                          + (f"  ej. {[(r['hora'], r['pc_vrp']) for r in cerca[:4]]}" if cerca else ""))
