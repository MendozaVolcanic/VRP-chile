# -*- coding: utf-8 -*-
"""Frente F (S146) F-03. Cuanto de lo que publicamos sobrevive al piso de VRP por sensor
que MIROVA declara en la Tabla 1 de Coppola et al. 2026 (Sci Data, p. idx 7 del PDF).

Tabla 1, fila "Nighttime VRP threshold (W)": MODIS 1.0e5 W, VIIRS 750 m 5.0e6 W,
VIIRS 375 m 1.0e4 W. Nuestros pisos efectivos son 0.0 en los tres
(MIN_VRP_MW_{MODIS,VIIRS375,VIIRS750}, leidos de pipeline.profile con VRP_PROFILE=mirova_equivalent).

SALVEDAD (A105): esa tabla es del producto de archivo OSF v2.5, que es filtrado y no es el
canal NRT que nosotros clonamos. El numero no prueba que el NRT de MIROVA use ese piso. Lo
que mide este script es el TAMANO del efecto si se aplicara, no que haya que aplicarlo.

Universo: los records de la ventana de la Fase 1 (2026-09-01 a 2026-09-20), todos los
volcanes en disco, solo pasadas nocturnas (el pipeline solo procesa noche).
"""
import json, glob, os, sys
sys.stdout.reconfigure(encoding='utf-8')

UMBRAL_MW = {'MODIS': 1.0e5/1e6, 'VIIRS750': 5.0e6/1e6, 'VIIRS375': 1.0e4/1e6}
base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'mirova_equivalent')
VENT0, VENT1 = '2026-09-01', '2026-09-21'

def magnitud(r, b):
    """La magnitud que el operador ve: f5_core en I-band, primary_cluster en el resto."""
    if b == 'VIIRS375' and r.get('f5_core_vrp_mw') is not None:
        return float(r['f5_core_vrp_mw'])
    pc = r.get('primary_cluster') or {}
    v = pc.get('vrp_mw')
    return float(v) if v is not None else None

acc = {}
for f in sorted(glob.glob(os.path.join(base, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for r in (d.get('records', d) if isinstance(d, dict) else d):
        dt = r.get('datetime_utc') or ''
        if not (VENT0 <= dt[:10] < VENT1): continue
        sn = r.get('sensor') or '?'
        b = 'MODIS' if sn.startswith('MODIS') else ('VIIRS750' if sn.endswith('750') else 'VIIRS375')
        v = magnitud(r, b)
        e = acc.setdefault(b, {'n': 0, 'con_mag': 0, 'summit': 0, 'summit_sobre': 0})
        e['n'] += 1
        if v is None: continue
        e['con_mag'] += 1
        pc = r.get('primary_cluster') or {}
        # proxy del predicado del dashboard: cumulo con clase summit y magnitud > 0
        if r.get('distance_class') == 'summit' and v > 0:
            e['summit'] += 1
            if v >= UMBRAL_MW[b]: e['summit_sobre'] += 1

print('Ventana 2026-09-01 a 2026-09-20, pasadas nocturnas, todos los volcanes en disco.')
print('PROXY del predicado de publicacion: distance_class == summit y magnitud > 0.')
print('NO es el predicado exacto del dashboard (ese lo corre la Fase 1 con node): es una cota.\n')
print(f"{'sensor':10s} {'piso MW':>9s} {'n pasadas':>10s} {'proxy publ.':>12s} {'sobreviven':>11s} {'% que sobrevive':>16s}")
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    e = acc.get(b)
    if not e: continue
    p = 100*e['summit_sobre']/e['summit'] if e['summit'] else float('nan')
    print(f"{b:10s} {UMBRAL_MW[b]:9.3f} {e['n']:10d} {e['summit']:12d} {e['summit_sobre']:11d} {p:15.1f}%")
