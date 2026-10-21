# M1 T2. Pregunta 1: si las ventanas que usaron F3/F4/V3/F1 (marzo a octubre 2026) mezclaran detectores o
# regimenes (#535 2026-08-28 23:00 UTC, K #850), esta tabla lo mostraria: cuenta records por mes y por
# codigo_sha de regimen en los 11 Tier A. Pregunta 2: si el campo regimen no existiera/estuviera vacio, el
# resultado seria 'None' y se veria (SIN DATO). Control positivo: la tabla debe mostrar mas de un sha (si
# mostrara uno solo seria sospechoso de columna constante).
import json,collections,sys,yaml,subprocess
root='.'
vy=yaml.safe_load(open('volcanoes.yaml',encoding='utf-8'))
vols=vy['volcanoes'] if isinstance(vy,dict) and 'volcanoes' in vy else vy
tier=[]
for v in (vols if isinstance(vols,list) else vols.values()):
    if isinstance(v,dict) and v.get('radius_km')==25: tier.append(v.get('name') or v.get('id'))
print('Tier A (radius_km 25):',len(tier),tier)
import glob,os
cnt=collections.defaultdict(collections.Counter)  # (mes,sensorclass)->sha
shas=collections.Counter()
sens=collections.Counter()
for f in glob.glob('data/mirova_equivalent/*.json'):
    nm=os.path.basename(f)[:-5]
    d=json.load(open(f,encoding='utf-8'))
    for r in d['records']:
        s=r['sensor']; sens[s]+=1
        if s.startswith('MODIS'): sc='MODIS'
        elif s.endswith('_750'): sc='V750'
        else: sc='V375'
        dt=r['datetime_utc']
        mes=dt[:7]
        sha=(r.get('regimen') or {}).get('codigo_sha')
        sha=sha[:8] if sha else None
        cnt[(mes,sc)][sha]+=1; shas[sha]+=1
print('sensores:',dict(sens))
print('n shas distintos:',len(shas))
for k in sorted(cnt):
    if k[0]>='2026-01': print(k, dict(cnt[k].most_common(6)), 'otros',max(0,len(cnt[k])-6))
print('top shas global:',shas.most_common(12))
