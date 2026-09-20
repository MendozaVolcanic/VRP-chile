# -*- coding: utf-8 -*-
"""Frente F (S146) F-01. El Test 1 integrado dispara con ruido puro, y el umbral al que
lo hace depende del TAMANO DE PIXEL. Comprobacion analitica + medicion sobre records.

EL FENOMENO. El criterio absoluto del Test 1 integrado (pipeline/test1_integrated.py
l. 420-435) suma el exceso POSITIVO de radiancia de cada pixel del ROI y lo compara contra
3 veces sigma_bg * raiz(N_ROI):

    delta_L = suma sobre el ROI de  max(0, L - L_bg)
    dispara si delta_L > k_sigma * sigma_bg * raiz(N_ROI)

Como el recorte max(0, .) tira la mitad negativa, el ruido puro NO suma cero: si el ruido
es normal de desvio sigma_bg, la media de max(0, ruido) es sigma_bg/raiz(2*pi) = 0,3989
sigma_bg. Entonces, sobre una escena SIN nada caliente:

    delta_L esperado = 0,3989 * sigma_bg * N_ROI
    k observado      = delta_L / (sigma_bg * raiz(N_ROI)) = 0,3989 * raiz(N_ROI)

El numerador crece como N y el umbral como raiz(N). El criterio deja de depender de si hay
calor y pasa a depender de cuantos pixeles entran en el ROI, o sea del tamano de pixel.
Cruce con k_sigma = 3: raiz(N_ROI) > 3/0,3989 = 7,52  ->  N_ROI > 56,5 pixeles.

Prediccion por sensor con ROI de radio TEST1_ROI_KM = 3 km (area 28,274 km2).
La medicion contrasta esa prediccion contra `test1_k_observed`, que el pipeline persiste.
"""
import json, glob, os, sys, math, statistics as st
sys.stdout.reconfigure(encoding='utf-8')

ROI_KM, K_SIGMA = 3.0, 3.0
HALF_NORMAL = 1.0 / math.sqrt(2 * math.pi)   # 0,39894
AREA_PIX_KM2 = {'MODIS': 1.0, 'VIIRS750': 0.75**2, 'VIIRS375': 0.375**2}
area_roi = math.pi * ROI_KM**2

print(f'ROI de radio {ROI_KM} km = {area_roi:.3f} km2 ; k_sigma = {K_SIGMA}')
print(f'media de max(0, ruido normal) = {HALF_NORMAL:.5f} * sigma')
print(f'cruce teorico: N_ROI > {(K_SIGMA/HALF_NORMAL)**2:.1f} pixeles\n')
print(f"{'sensor':10s} {'A_pix km2':>10s} {'N_ROI':>7s} {'k pred. solo ruido':>19s} {'dispara con ruido':>19s}")
pred = {}
for s, a in AREA_PIX_KM2.items():
    n = area_roi / a
    k = HALF_NORMAL * math.sqrt(n)
    pred[s] = (n, k)
    print(f"{s:10s} {a:10.4f} {n:7.1f} {k:19.2f} {('SI' if k > K_SIGMA else 'no'):>19s}")

base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'mirova_equivalent')
obs = {}
for f in sorted(glob.glob(os.path.join(base, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for r in (d.get('records', d) if isinstance(d, dict) else d):
        sn = r.get('sensor') or '?'
        b = 'MODIS' if sn.startswith('MODIS') else ('VIIRS750' if sn.endswith('750') else 'VIIRS375')
        k, t = r.get('test1_k_observed'), r.get('triggered_test1')
        if k is None: continue
        try: k = float(k)
        except Exception: continue
        if k != k or k <= 0: continue
        e = obs.setdefault(b, {'k': [], 'trig': 0, 'n': 0})
        e['k'].append(k); e['n'] += 1
        if t: e['trig'] += 1

print(f"\nMEDIDO sobre data/mirova_equivalent (todos los volcanes, 2025-02 a 2026-09),")
print(f"records con test1_k_observed > 0:")
print(f"{'sensor':10s} {'n':>7s} {'k mediana':>10s} {'k p25':>8s} {'k p75':>8s} {'k predicho':>11s} {'% triggered_test1':>18s}")
for s in ('MODIS', 'VIIRS750', 'VIIRS375'):
    e = obs.get(s)
    if not e: print(f'{s:10s} SIN DATO'); continue
    ks = sorted(e['k']); n = len(ks)
    q = lambda p: ks[min(n-1, int(p*n))]
    print(f"{s:10s} {n:7d} {st.median(ks):10.2f} {q(.25):8.2f} {q(.75):8.2f} "
          f"{pred[s][1]:11.2f} {100*e['trig']/e['n']:17.1f}%")
