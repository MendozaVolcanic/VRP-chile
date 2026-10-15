import json,sys,collections,statistics,math
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(sys.argv[1])
filas=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.rglob('*.json'))]
print(len(filas), collections.Counter(f['clase'] for f in filas))
print('keys', list(filas[0].keys()))
f=filas[0]; print(json.dumps({k:f[k] for k in f if k not in('control','a','b')},ensure_ascii=False)[:800])
print(json.dumps(f['a']['llamadas_fondo'],ensure_ascii=False)[:1500])
print(json.dumps(f['a']['record'].get('primary_cluster'),ensure_ascii=False)[:800])
print('src',f['control']['record'].get('final_hotspot_source'), f['a']['record'].get('final_hotspot_source'))
