# -*- coding: utf-8 -*-
"""Frente F (S146). Cierra los dos SIN DATO baratos: el numero de intentos (F-02) y la
dependencia con el angulo cenital (F-04).

F-02b. Si la sobre-publicacion contextual se explicara por "mas pixeles, mas cruces", la
TASA de pixeles marcados por pixel evaluado deberia ser parecida entre sensores y el total
deberia seguir al numero de pixeles. Se mide como diag_n_first_pass_pixels dividido por
diag_n_bg_used_first_pass (el numero de pixeles que de verdad entraron al calculo de mu y
sigma, que es el proxy persistido del tamano del ROI evaluado).

F-04b. Si no remuestrear duele por bow-tie y anisotropia, el efecto tiene que CRECER con el
angulo cenital en VIIRS y ser plano en MODIS. Se mide la tasa de un proxy de publicacion
(distance_class summit y magnitud > 0) por tramo de sensor_zenith_deg.

PROXY declarado: no es el predicado del dashboard (ese lo corre la Fase 1 con node), y el
universo NO esta restringido a negativos limpios. Sirve para ver una TENDENCIA, no un nivel.
"""
import json, glob, os, sys, statistics as st
sys.stdout.reconfigure(encoding='utf-8')

base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'mirova_equivalent')
TRAMOS = [(0, 20), (20, 35), (35, 45), (45, 55), (55, 90)]
f02, f04 = {}, {}
for f in sorted(glob.glob(os.path.join(base, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for r in (d.get('records', d) if isinstance(d, dict) else d):
        sn = r.get('sensor') or '?'
        b = 'MODIS' if sn.startswith('MODIS') else ('VIIRS750' if sn.endswith('750') else 'VIIRS375')
        fp, nbg = r.get('diag_n_first_pass_pixels'), r.get('diag_n_bg_used_first_pass')
        if fp is not None and nbg:
            try: f02.setdefault(b, []).append(float(fp)/float(nbg))
            except Exception: pass
        z = r.get('sensor_zenith_deg')
        if z is None: continue
        try: z = float(z)
        except Exception: continue
        if z != z: continue
        v = r.get('f5_core_vrp_mw') if b == 'VIIRS375' else None
        if v is None:
            v = (r.get('primary_cluster') or {}).get('vrp_mw')
        pub = (r.get('distance_class') == 'summit') and (v is not None) and (float(v) > 0)
        for lo, hi in TRAMOS:
            if lo <= abs(z) < hi:
                e = f04.setdefault((b, (lo, hi)), [0, 0]); e[0] += 1; e[1] += int(pub)
                break

print('F-02b. Tasa de pixeles marcados por el primer pase, sobre los pixeles evaluados.')
print(f"{'sensor':10s} {'n records':>10s} {'tasa mediana':>13s} {'tasa media':>11s}")
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    v = f02.get(b)
    if not v: continue
    print(f"{b:10s} {len(v):10d} {st.median(v):13.6f} {sum(v)/len(v):11.6f}")
print('\nSi mandara el numero de intentos, la tasa seria PAREJA entre sensores.')

print('\nF-04b. Proxy de publicacion por tramo de angulo cenital (NO son negativos limpios).')
print(f"{'sensor':10s} " + ''.join(f"{str(t):>14s}" for t in TRAMOS))
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    fila = f"{b:10s} "
    for t in TRAMOS:
        e = f04.get((b, t))
        fila += (f"{100*e[1]/e[0]:11.1f}% " if e and e[0] >= 30 else f"{'n<30':>13s} ")
    print(fila)
print('n por celda:')
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    print(f"  {b:10s}", {str(t): (f04.get((b, t)) or [0, 0])[0] for t in TRAMOS})
