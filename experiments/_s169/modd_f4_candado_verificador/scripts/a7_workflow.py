# P1: si el workflow tuviera un trigger extra, un push/commit, un secreto distinto o permisos de escritura, este analisis lo veria? Si: parsea el YAML con PyYAML y busca patrones en cada run.
# P2: control positivo: aplico el mismo analisis a nrt.yml (que SI tiene schedule, push, USERNAME/PASSWORD) y debe marcarlos; si no, el analisis esta muerto.
import yaml, re, sys, json
R='D:/vrp-trabajo/temporales/s169_ver_candado/arbol/.github/workflows/'
def analizar(nombre):
    txt=open(R+nombre,encoding='utf-8').read()
    y=yaml.safe_load(txt)
    claves=list(y.keys())
    on = y.get('on', y.get(True))
    out={'archivo':nombre,'claves_toplevel':[repr(k) for k in claves],'on_es_str':('on' in y),'on':on if not isinstance(on,dict) else list(on.keys()),
         'permissions_toplevel':y.get('permissions'),'concurrency':y.get('concurrency'),'env_toplevel':list((y.get('env') or {}).keys())}
    secretos=sorted(set(re.findall(r'secrets\.([A-Za-z0-9_]+)',txt)))
    out['secretos']=secretos
    jobs={}
    for jn,j in (y.get('jobs') or {}).items():
        runs='\n'.join((s.get('run') or '') for s in j.get('steps',[]))
        jobs[jn]={'runs-on':j.get('runs-on'),'timeout':j.get('timeout-minutes'),'permissions':j.get('permissions'),'needs':j.get('needs'),'if':j.get('if'),
                  'push/commit/add':bool(re.search(r'git\s+(push|commit|add|tag)\b',runs)),
                  'escribe data/':bool(re.search(r'(>|>>|tee|cp|mv|mkdir|rm)\s+[^\n]*\bdata/',runs)),
                  'usa gh/curl':bool(re.search(r'\b(gh|curl|wget)\b',runs)),
                  'env_job':list((j.get('env') or {}).keys()),
                  'usos':[s.get('uses') for s in j.get('steps',[]) if s.get('uses')]}
    out['jobs']=jobs
    out['USERNAME/PASSWORD'] = bool(re.search(r'EARTHDATA_(USERNAME|PASSWORD)',txt))
    out['contiene_persist_credentials']='persist-credentials' in txt
    return out
for n in sys.argv[1:]:
    print(json.dumps(analizar(n),ensure_ascii=False,indent=1,default=str)); print('-----')
