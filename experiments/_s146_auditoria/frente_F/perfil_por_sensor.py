# -*- coding: utf-8 -*-
"""Frente F (S146). Perfil comparado de los tres sensores sobre records ya persistidos.

POR QUE: la brecha de sobre-publicacion esta en VIIRS. Este script mide, por sensor y sin
tocar el pipeline, las magnitudes que gobiernan la cascada de deteccion, para ver cual se
comporta distinto entre MODIS (donde el umbral fue calibrado) y VIIRS (donde se copio).

Universo: todos los records de data/mirova_equivalent/*.json. Ventana: la que haya en disco
(se imprime el rango de fechas). Sin filtrar por volcan ni por alerta.
"""
import json, glob, os, sys, statistics as st
sys.stdout.reconfigure(encoding='utf-8')

base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'mirova_equivalent')
CAMPOS = ['diag_sd_dnti', 'diag_sd_deti', 'diag_n_bg_anillo', 'diag_n_bg_used_first_pass',
          'diag_n_dnti_ctx_path', 'diag_n_eti_path', 'diag_n_first_pass_pixels',
          'diag_n_second_pass_recapture', 'diag_n_bt_path', 'n_test1_pixels',
          'n_anomalous_pixels', 'n_nti_anomalous', 'diag_sigma_bg_k', 'vrp_mw',
          'sensor_zenith_deg']
por = {}
fechas = {}
for f in sorted(glob.glob(os.path.join(base, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    rs = d.get('records', d) if isinstance(d, dict) else d
    for r in rs:
        s = r.get('sensor') or '?'
        b = 'MODIS' if s.startswith('MODIS') else ('VIIRS750' if s.endswith('750') else 'VIIRS375')
        e = por.setdefault(b, {c: [] for c in CAMPOS})
        e.setdefault('__n__', [0])[0] += 1
        dt = r.get('datetime_utc')
        if dt:
            fx = fechas.setdefault(b, [dt, dt])
            fx[0] = min(fx[0], dt); fx[1] = max(fx[1], dt)
        for c in CAMPOS:
            v = r.get(c)
            if v is None: continue
            try: v = float(v)
            except Exception: continue
            if v == v: e[c].append(v)

def med(x): return st.median(x) if x else float('nan')
sens = [b for b in ('MODIS', 'VIIRS750', 'VIIRS375') if b in por]
print('records por sensor:', {b: por[b]['__n__'][0] for b in sens})
print('ventana de fechas :', {b: fechas.get(b) for b in sens})
print()
print(f"{'campo':32s}" + ''.join(f"{b:>14s}" for b in sens) + '   (mediana, n)')
for c in CAMPOS:
    fila = f"{c:32s}"
    for b in sens:
        fila += f"{med(por[b][c]):14.4f}"
    fila += '   n=' + '/'.join(str(len(por[b][c])) for b in sens)
    print(fila)
print()
print('fraccion de records con al menos 1 pixel por camino:')
for c in ['diag_n_dnti_ctx_path', 'diag_n_eti_path', 'diag_n_bt_path',
          'diag_n_first_pass_pixels', 'n_test1_pixels', 'diag_n_second_pass_recapture']:
    fila = f"{c:32s}"
    for b in sens:
        v = por[b][c]
        fila += f"{(100*sum(1 for x in v if x > 0)/len(v) if v else float('nan')):13.1f}%"
    print(fila)
