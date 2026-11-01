# M1 T2b. Para cada record de los 11 Tier A: su codigo_sha, y si ese commit es descendiente de #535 (1888c1e3e)
# y de K (34cea39e). Pregunta 1: si las ventanas mezclaran detectores, 'sin_K' o 'sin_535' serian > 0 en el tramo
# 2026-03..2026-10. Pregunta 2: sha None cuenta aparte (SIN DATO), no como OK. Control positivo: debe haber al
# menos un sha anterior a #535 en 2025 (si no hay ninguno el chequeo de ancestria estaria muerto).
import json,collections,subprocess,os
TIER=['PuyehueCordonCaulle','Villarrica','Lascar','Copahue','NevadosDeChillan','Llaima','Chaiten','PlanchonPeteroa','Lastarria','Isluga','Tupungatito']
def anc(a,b):
    return subprocess.run(['git','merge-base','--is-ancestor',a,b],capture_output=True).returncode==0
K='34cea39e'; C535='1888c1e3e'
cache={}
def cls(sha):
    if sha is None: return 'SIN_REGIMEN'
    if sha in cache: return cache[sha]
    r=subprocess.run(['git','cat-file','-t',sha],capture_output=True,text=True)
    if r.returncode!=0: cache[sha]='SHA_NO_RESUELVE'; return cache[sha]
    k=anc(K,sha) ; c=anc(C535,sha)
    cache[sha]=('K' if k else 'preK')+('+535' if c else '-535')
    return cache[sha]
tab=collections.defaultdict(collections.Counter)
for v in TIER:
    d=json.load(open(f'data/mirova_equivalent/{v}.json',encoding='utf-8'))
    for r in d['records']:
        s=r['sensor']
        sc='MODIS' if s.startswith('MODIS') else ('V750' if s.endswith('_750') else 'V375')
        sha=(r.get('regimen') or {}).get('codigo_sha')
        sha=sha[:8] if sha else None
        tab[(r['datetime_utc'][:7],sc)][cls(sha)]+=1
for k in sorted(tab):
    if k[0]>='2025-02': print(k, dict(tab[k]))
print('clases de sha:',collections.Counter(cache.values()))
