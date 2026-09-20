# -*- coding: utf-8 -*-
"""Frente F (S146) F-01, prueba independiente por angulo cenital.

LA PREDICCION. Si el Test 1 integrado dispara por RUIDO y su valor de reposo es
k = 0,3989 * raiz(N_ROI), entonces al alejarse del nadir el pixel VIIRS crece, caben MENOS
pixeles en el disco de 3 km, y k tiene que BAJAR. No por menos calor: por menos pixeles.

Es una prediccion con signo y con tamano, y no la hace ninguna otra explicacion de la
sobre-publicacion. Si k fuera una medida de calor, no tendria por que depender del angulo
con que el satelite mira el mismo volcan la misma noche.

Tamano esperado en VIIRS I-band: el ATBD de geolocalizacion (423-ATBD-002, Tabla 2.2-1,
citado en pipeline/scan_geometry.py l. 210-214) da el area del pixel de 0,144 km2 en nadir
a 0,631 km2 en el borde del swath, factor 4,38. Como k va con raiz(N_ROI) y N_ROI va con
1/area, k tiene que caer por un factor raiz(4,38) = 2,09 de nadir a borde.

En MODIS el area tambien crece con el angulo, asi que el mismo efecto debe verse, y en el
mismo sentido. Lo que NO puede pasar, si la explicacion es el calor, es que k dependa del
angulo de forma ordenada en los tres sensores a la vez.
"""
import json, glob, os, sys, math, statistics as st
sys.stdout.reconfigure(encoding='utf-8')

base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'mirova_equivalent')
TRAMOS = [(0, 15), (15, 30), (30, 42), (42, 52), (52, 62), (62, 90)]
acc = {}
for f in sorted(glob.glob(os.path.join(base, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for r in (d.get('records', d) if isinstance(d, dict) else d):
        sn = r.get('sensor') or '?'
        b = 'MODIS' if sn.startswith('MODIS') else ('VIIRS750' if sn.endswith('750') else 'VIIRS375')
        z, k = r.get('sensor_zenith_deg'), r.get('test1_k_observed')
        if z is None or k is None: continue
        try: z, k = abs(float(z)), float(k)
        except Exception: continue
        if z != z or k != k or k <= 0: continue
        for lo, hi in TRAMOS:
            if lo <= z < hi:
                acc.setdefault((b, (lo, hi)), []).append(k); break

print('Mediana de test1_k_observed por tramo de angulo cenital (grados).')
print('El umbral del criterio absoluto es 3,0: por debajo, el Test 1 no dispara solo con ruido.\n')
print(f"{'sensor':10s} " + ''.join(f"{f'{lo}-{hi}':>12s}" for lo, hi in TRAMOS) + f"{'caida':>9s}")
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    fila, prim, ult = f"{b:10s} ", None, None
    for t in TRAMOS:
        v = acc.get((b, t))
        if v and len(v) >= 30:
            m = st.median(v); fila += f"{m:12.2f}"
            if prim is None: prim = m
            ult = m
        else:
            fila += f"{'n<30':>12s}"
    fila += f"{(prim/ult if prim and ult else float('nan')):9.2f}x"
    print(fila)
print('\nn por celda:')
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    print(f"  {b:10s}", {f'{lo}-{hi}': len(acc.get((b, (lo, hi))) or []) for lo, hi in TRAMOS})
print(f"\nCaida predicha en VIIRS I-band de nadir a borde: raiz(4,38) = {math.sqrt(4.38):.2f}x")
