# -*- coding: utf-8 -*-
"""03e: alertas nocturnas de MIROVA (3 volcanes) sin record nuestro a +-120 s (cobertura, no geometria), con el mismo
indexado de 03. Corrido en la sesion como heredoc (salida en 03e_alertas_sin_record_salida.txt).
Uso: PYTHONIOENCODING=utf-8 python 03e_alertas_sin_record.py 2>/dev/null > 03e_alertas_sin_record_salida.txt
"""
import json
import os
import sys
from datetime import datetime, timezone

import comun as C

sys.path.insert(0, str(C.ROOT))
sys.path.insert(0, str(C.ROOT / 'scripts'))
os.environ.setdefault('VRP_PROFILE', 'mirova_equivalent')
import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

coords = {v: (C.GEO[v]['lat'], C.GEO[v]['lon']) for v in C.VOLS}
filas = [f for f in cargar_referencia_unificada() if f['volcano'] in C.VOLS]
por_vb, ns, nv, n = BP.indexar_referencia(filas, coords, ('2026-01-10', '2026-10-21'), regla_minimas='SN')
recs = []
for v in C.VOLS:
    for r in json.load(open(C.DATA / f'{v}.json', encoding='utf-8'))['records']:
        b = C.bucket(r.get('sensor'))
        if not b or not ('2026-01-10' <= r['datetime_utc'][:10] <= '2026-10-21'):
            continue
        dt = datetime.strptime(r['datetime_utc'], '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        if BP.es_pasada_diurna_descartada(b, *coords[v], dt):
            continue
        recs.append({'vol': v, 'b': b, 'dt': dt})
sr = BP.alertas_sin_record(por_vb, recs)
print('alertas nocturnas de MIROVA sin record nuestro a +-120 s, por (volcan, sensor):', {str(k): v for k, v in sr.items()})
tot = {}
for (v, b), L in por_vb.items():
    tot[(v, b)] = sum(1 for dt, f in L if BP.es_alerta(f['tipo']))
print('alertas nocturnas totales por (volcan, sensor) en la ventana (filas, CONS y OCR por separado):', {str(k): v for k, v in sorted(tot.items())})
