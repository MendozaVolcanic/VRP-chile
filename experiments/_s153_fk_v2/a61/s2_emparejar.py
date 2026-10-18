# -*- coding: utf-8 -*-
"""Paso 2: emparejar cada movida con los TIF de MIROVA por HORA DE ADQUISICION (A106), +-15 min mismo sensor;
md5 repetido = imagen reciclada (no propia). Ademas TIF de otras pasadas de la misma noche (A109), 45-120 min."""
import csv, json, sys
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open('index.csv', encoding='utf-8')))
T = json.load(open('s1_tabla.json', encoding='utf-8'))
p = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
idx = {}
for r in rows:
    if not r['acquisition_utc'] or not r['size_bytes'] or int(r['size_bytes']) == 0: continue
    idx.setdefault((r['volcano'], r['sensor']), []).append((p(r['acquisition_utc']), r))
for k in idx: idx[k].sort(key=lambda x: x[0])
primera = {}
for k in idx:
    for t, r in idx[k]:
        if r['md5'] not in primera or t < primera[r['md5']]: primera[r['md5']] = t
out = []
for m in T:
    t = datetime.strptime(m['t'], '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
    L = idx.get((m['vol'], m['s']), [])
    cand = sorted([(abs((a - t).total_seconds()), i) for i, (a, r) in enumerate(L)])
    near = None
    if cand:
        d, i = cand[0]; a, r = L[i]
        near = {"dt_s": round((a - t).total_seconds()), "acq": a.isoformat(), "tif": r['tif_path'], "md5": r['md5'],
                "propia": primera[r['md5']] == a, "dentro15": d <= 900}
    otras = []
    for s in ('VIIRS375', 'VIIRS750', 'MODIS'):
        for a, r in idx.get((m['vol'], s), []):
            dd = (a - t).total_seconds()
            if 45 * 60 <= abs(dd) <= 120 * 60:
                otras.append({"dt_min": round(dd / 60), "sensor": s, "acq": a.isoformat(), "tif": r['tif_path'], "md5": r['md5'],
                              "propia": primera[r['md5']] == a})
    out.append({"k": m['k'], "near": near, "otras": otras})
    if near and abs(near['dt_s']) < 6 * 3600:
        print(m['k'], near['dt_s'], near['tif'], 'propia' if near['propia'] else 'RECICLADA', '| otras', [(o['dt_min'], o['sensor'], o['propia']) for o in otras])
json.dump(out, open('s2_emparejar.json', 'w', encoding='utf-8'), indent=1)
print('con TIF +-15 min:', sum(1 for o in out if o['near'] and o['near']['dentro15']))
