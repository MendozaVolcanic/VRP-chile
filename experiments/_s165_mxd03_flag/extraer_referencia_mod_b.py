# -*- coding: utf-8 -*-
"""S165, Tarea 4: copia a referencia_mod_b.jsonl los brazos K y X (y su publicacion) de los records de los 5 granulos del
humo, desde los artefactos de MOD-B bajados a D:/vrp-trabajo/temporales/s162_mxd03 (t1, t2, t3: runs 40112510038,
40122029477, 40126381034). La carpeta `tandas` repite las mismas partes: no se lee (la primera version la leia y
duplicaba los 18 records). La cabecera guarda el sha256 de cada archivo fuente.

Uso (desde D:/vrp-trabajo/temporales/s162_mxd03): python extraer_referencia_mod_b.py <destino.jsonl>
"""
import json, glob, hashlib, collections, sys
from pathlib import Path
G = ["MYD021KM.A2026073.0705", "MYD021KM.A2026086.0710", "MYD021KM.A2026283.0740", "MOD021KM.A2026284.0140",
     "MOD021KM.A2026113.0150"]
dest = sys.argv[1]
out, fuentes = [], {}
for f in sorted(glob.glob('t[123]/run_*/*/ab_parte*.jsonl')):
    b = open(f, 'rb').read()
    for l in b.decode('utf-8').splitlines():
        r = json.loads(l)
        if r.get('tipo') == 'record' and r.get('clave') in G:
            d = {k: r.get(k) for k in ('tipo', 'clave', 'vol', 'dt', 'sensor', 'lab', 'inner', 'n_fill_mxd03', 'estado')}
            d['brazos'] = {k: r['brazos'][k] for k in ('K', 'X')}
            d['pub'] = {k: r['pub'][k] for k in ('K', 'X')}
            out.append(d)
            fuentes[Path(f).as_posix()] = hashlib.sha256(b).hexdigest()
cab = {"tipo": "cabecera", "que": "brazos K y X y su publicacion, records de los 5 granulos del humo, copiados de los artefactos de MOD-B (S162)",
       "fuentes_sha256": fuentes, "runs": ["40122029477", "40126381034"], "n": len(out)}
with open(dest, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(json.dumps(cab, ensure_ascii=False) + "\n")
    for r in out:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(out), collections.Counter(r['estado'] for r in out), collections.Counter(r['clave'] for r in out))
print(sum(r['brazos']['K'] != r['brazos']['X'] for r in out), 'con K distinto de X;',
      sum(r['pub']['K'] != r['pub']['X'] for r in out), 'con publicacion distinta')
print([(r['vol'], r['n_fill_mxd03']) for r in out if r['clave'] == 'MOD021KM.A2026113.0150'])
