# -*- coding: utf-8 -*-
"""Paso 3: elegir y bajar TIF de a uno por la API (sin clonar). Por movida: la imagen de la propia pasada (+-15 min,
aunque sea reciclada, para decirlo) y hasta 1 de otras pasadas de la misma noche (45-120 min, md5 propio,
prefiriendo VIIRS 375). Tope 45 archivos."""
import json, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
E = json.load(open('s2_emparejar.json', encoding='utf-8'))
want = []
for e in E:
    n = e['near']
    if n and n['dentro15']: want.append(n['tif'])
    pref = {'VIIRS375': 0, 'VIIRS750': 1, 'MODIS': 2}
    ot = sorted([o for o in e['otras'] if o['propia']], key=lambda o: (pref[o['sensor']], abs(o['dt_min'])))
    seen = set()
    for o in ot:
        if o['md5'] in seen: continue
        seen.add(o['md5']); want.append(o['tif'])
        if len(seen) == 1: break
want = list(dict.fromkeys(want))
print(len(want))
assert len(want) <= 45
for t in want:
    dst = Path('tif') / t.replace('data/tif/', '').replace('/', '_')
    if dst.exists() and dst.stat().st_size > 0: continue
    b = subprocess.run(['gh', 'api', '-H', 'Accept: application/vnd.github.raw', 'repos/MendozaVolcanic/mirova-tif-archive/contents/' + t], capture_output=True)
    if b.returncode: print('FALLA', t, b.stderr[:200]); continue
    dst.write_bytes(b.stdout)
print(len(list(Path('tif').glob('*.tif'))))
