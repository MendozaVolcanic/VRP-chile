# Censo de regimen por fecha de observacion, 11 Tier A.
# Pregunta 1: si la marca de regimen estuviera rota (todos K o todos C0), lo veria? Si: cuento por sha y ancestria.
# Pregunta 2: instrumento muerto -> records sin 'regimen' se cuentan aparte como SIN_MARCA (no se confunden con C0).
# Control positivo: el sha 34cea39e mismo debe salir K; un sha viejo (pre-merge) debe salir C0.
import json, subprocess, collections, sys, os
R = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(R, '..', '..', '..'))
TIER = ['Lascar','Lastarria','Isluga','Tupungatito','PlanchonPeteroa','NevadosDeChillan','Copahue','Llaima','Villarrica','PuyehueCordonCaulle','Chaiten']
K = '34cea39e4b64f0862e4bad949016a57ea181f8c4'
cache = {}
def es_k(sha):
    if sha in cache: return cache[sha]
    r = subprocess.run(['git','-C',REPO,'merge-base','--is-ancestor',K,sha],capture_output=True)
    cache[sha] = {0:'K',1:'C0'}.get(r.returncode,'SHA_DESCONOCIDO')
    return cache[sha]
print('control +: K->', es_k(K), '; padre de K ->', es_k(subprocess.check_output(['git','-C',REPO,'rev-parse',K+'^']).decode().strip()))
porvol = {}
for v in TIER:
    d = json.load(open(os.path.join(REPO,'data','mirova_equivalent',v+'.json'),encoding='utf-8'))
    c = collections.Counter()
    pordia = collections.defaultdict(collections.Counter)
    for r in d['records']:
        g = r.get('regimen') or {}
        sha = g.get('codigo_sha')
        reg = es_k(sha) if sha else 'SIN_MARCA'
        day = r['datetime_utc'][:10]
        pordia[day][reg]+=1
        c[(reg, day>='2026-09-18')]+=1
    porvol[v]=pordia
    # primer dia con K y ultimo dia con C0/sin marca
    kdays = sorted(dd for dd,cc in pordia.items() if cc['K'])
    mix = sorted(dd for dd,cc in pordia.items() if cc['K'] and (cc['C0'] or cc['SIN_MARCA']))
    print(v, dict(c), 'primer_dia_K', kdays[0] if kdays else None, 'dias_mixtos', len(mix), mix[:6])
print('shas:', {k[:8]:v for k,v in cache.items()})
json.dump({v:{dd:dict(cc) for dd,cc in p.items()} for v,p in porvol.items()}, open(os.path.join(R,'censo_regimen.json'),'w'))
