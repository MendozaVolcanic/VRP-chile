# -*- coding: utf-8 -*-
"""Frente F (S146). Cuanto vale, en sigmas del propio sensor, el piso absoluto C1=0.003.

POR QUE: C1 y C2 salen de la Tabla 1 de Coppola 2016a, calibrada sobre MODIS 1 km.
Campus 2022 (Sensors 22:1713, p.7) dice que el detector de VIIRS es "the same used for
MODIS", pero no vuelve a calibrar C1. Si sigma_dNTI difiere entre sensores, el MISMO
C1 es un umbral distinto en cada uno. Esto lo mide sobre records ya persistidos.

Definiciones dentro de la afirmacion (A90):
  - universo: todos los records de data/mirova_equivalent/*.json con diag_sd_dnti finito.
  - sensor: el campo `sensor` tal cual (I-band = VIIRS_* sin sufijo; M-band = *_750).
  - manda_C1: True si C1_summit(0.003) < mu_dnti + C2_summit(5)*sd_dnti, es decir si la
    rama OR de los Tests 2/3 queda decidida por el piso absoluto y no por la estadistica.
"""
import json, glob, os, sys, statistics as st
sys.stdout.reconfigure(encoding='utf-8')

C1_SUMMIT, C1_SCENE, C2_SUMMIT, C2_SCENE = 0.003, 0.010, 5.0, 10.0
base = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'mirova_equivalent')
por = {}
for f in sorted(glob.glob(os.path.join(base, '*.json'))):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print('SKIP', f, e); continue
    rs = d.get('records', d) if isinstance(d, dict) else d
    for r in rs:
        s = r.get('sensor') or '?'
        b = 'MODIS' if s.startswith('MODIS') else ('VIIRS750' if s.endswith('750') else 'VIIRS375')
        sd, mu = r.get('diag_sd_dnti'), r.get('diag_mu_dnti')
        if sd is None or mu is None: continue
        try: sd = float(sd); mu = float(mu)
        except Exception: continue
        if not (sd == sd and mu == mu) or sd <= 0: continue
        e = por.setdefault(b, {'sd': [], 'manda_s': 0, 'manda_e': 0, 'n': 0})
        e['sd'].append(sd); e['n'] += 1
        if C1_SUMMIT < mu + C2_SUMMIT * sd: e['manda_s'] += 1
        if C1_SCENE  < mu + C2_SCENE  * sd: e['manda_e'] += 1

print(f"{'sensor':10s} {'n':>7s} {'med sd_dNTI':>12s} {'C1s/sd':>8s} {'C1e/sd':>8s} {'%manda C1s':>11s} {'%manda C1e':>11s}")
for b in ('MODIS', 'VIIRS750', 'VIIRS375'):
    e = por.get(b)
    if not e: print(b, 'SIN DATO'); continue
    m = st.median(e['sd'])
    print(f"{b:10s} {e['n']:7d} {m:12.6f} {C1_SUMMIT/m:8.2f} {C1_SCENE/m:8.2f} "
          f"{100*e['manda_s']/e['n']:10.1f}% {100*e['manda_e']/e['n']:10.1f}%")
