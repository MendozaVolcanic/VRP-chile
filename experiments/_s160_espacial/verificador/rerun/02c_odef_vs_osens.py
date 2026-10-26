# -*- coding: utf-8 -*-
"""02c: en el censo S159 (VIIRS 750, 2026-04-01 a 2026-10-21), cuantas alertas de MIROVA de cada volcan marca el codigo de
MIROVA con la caja POR DEFECTO (O-def: cumbre 7 x 7 sensible, resto con umbrales de escena) y con el anillo sensible
(O-sens). Corrido en la sesion como heredoc (salida en 02c_odef_vs_osens_salida.txt); se guarda igual como instrumento.
P1: si el conteo estuviera roto, Isluga (crater en el centro) daria 0 con O-def. P2: n por celda impreso.
Uso: PYTHONIOENCODING=utf-8 python 02c_odef_vs_osens.py > 02c_odef_vs_osens_salida.txt
"""
import collections
import glob
import json

obj = {(o['volcan'], o['hora_utc']): o for o in json.load(open('../../_censo_s159/objetivos.json', encoding='utf-8'))}
res = []
for f in sorted(glob.glob('../../_censo_s159/censo_39713438252/*/resultados_*.json')):
    res += json.load(open(f, encoding='utf-8'))
c = collections.defaultdict(collections.Counter)
for r in res:
    if r.get('estado') != 'ok':
        continue
    o = obj.get((r['volcan'], r['hora_utc']), {})
    lab = o.get('lab')
    prot = o.get('protegida')
    od = (r.get('oraculo') or {}).get('geo_linear') or {}
    os_ = (r.get('oraculo') or {}).get('geo_linear_anillo_sensible') or {}
    k = r['volcan']
    c[k][f'{lab}_n'] += 1
    if od.get('npix', 0) > 0:
        c[k][f'{lab}_Odef'] += 1
    if os_.get('npix', 0) > 0:
        c[k][f'{lab}_Osens'] += 1
    if lab == 'pos' and prot:
        c[k]['prot_n'] += 1
        if od.get('npix', 0) > 0:
            c[k]['prot_Odef'] += 1
        if os_.get('npix', 0) > 0:
            c[k]['prot_Osens'] += 1
print("volcan: alertas pos (n, O-def marca, O-sens marca) | protegidas (n, O-def, O-sens) | neg_limpio (n, O-def, O-sens)")
for k in sorted(c):
    x = c[k]
    print(f"  {k:22s} pos {x['pos_n']:3d} / {x['pos_Odef']:3d} / {x['pos_Osens']:3d} | prot {x['prot_n']:2d} / {x['prot_Odef']:2d} / {x['prot_Osens']:2d} | neg {x['neg_limpio_n']:4d} / {x['neg_limpio_Odef']:2d} / {x['neg_limpio_Osens']:2d}")
