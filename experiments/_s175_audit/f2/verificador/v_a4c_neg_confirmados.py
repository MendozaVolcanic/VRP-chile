# -*- coding: utf-8 -*-
"""A4 (desglose): por que 53 negativos limpios publicados salen 'confirmados'. Port en Python de la regla de
enrichWithMirovaConfirmation (cls no NULO/RUTINA, VRP>0, bucket VIIRS375, +-60 min), validado contra el conteo con
node (53) antes de desglosar. Uso: python v_a4c_neg_confirmados.py <arbol> <json v_a1_a3>"""
import collections, json, sys
from datetime import datetime
from pathlib import Path
A = Path(sys.argv[1]); d = json.load(open(sys.argv[2], encoding='utf-8'))
mir = {}
for vol in {r['vol'] for r in d['v375']}:
    x = []
    for m in json.load(open(A/'data'/'mirova'/f'{vol}.json', encoding='utf-8'))['records']:
        cls = str(m.get('clasificacion') or '').upper()
        v = float(m.get('VRP_MW') or 0)
        if cls in ('NULO', 'RUTINA') or not v > 0 or str(m.get('sensor')).upper() != 'VIIRS375':
            continue
        x.append((datetime.strptime(m['datetime_utc'][:16], '%Y-%m-%d %H:%M'), v, m.get('source'), cls))
    mir[vol] = x
neg = [r for r in d['v375'] if r['lab'] == 'neg_limpio' and r['pub']]
c = collections.Counter(); ej = []
for r in neg:
    t = datetime.fromisoformat(r['dt']).replace(tzinfo=None)
    cerca = [(abs((a - t).total_seconds()) / 60, v, s, cl) for a, v, s, cl in mir[r['vol']] if abs((a - t).total_seconds()) <= 3600]
    if not cerca:
        continue
    c['confirmado'] += 1
    c['todas_minimas_<=0.05' if all(v <= 0.05 + 1e-9 for _, v, _, _ in cerca) else 'alguna_>0.05'] += 1
    c['la_mas_cercana_a_>120s' if min(x[0] for x in cerca) > 2 else 'alguna_a_<=120s'] += 1
    c['otro_dia_utc' if all(datetime.fromisoformat(r['dt']).date() != (t).date() for _ in [0]) else 'x'] += 0
    if len(ej) < 6:
        ej.append((r['vol'], r['sensor'], r['dt'][:16], sorted((round(m, 1), v, s, cl) for m, v, s, cl in cerca)[:3]))
print('neg_limpio publicados', len(neg), dict(c))
for e in ej:
    print('  ', e)
