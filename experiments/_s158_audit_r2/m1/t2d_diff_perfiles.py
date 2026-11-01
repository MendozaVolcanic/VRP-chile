# M1 T2d. Pregunta 1: si el perfil del reproceso historico (_s154_reproc_k_historico) difiriera del de produccion en
# algun flag efectivo, los records anteriores al 2026-09-18 no serian 'de K en produccion' y las ventanas de marzo a
# septiembre (F3, F4, V3) mezclarian dos detectores. Esta comparacion lo veria. Pregunta 2: si el import fallara,
# el script imprime el error y sale 1 (no un 'sin diferencias'). Control positivo: se compara tambien contra el
# perfil 'experimental', que se sabe distinto (debe dar >0 diferencias).
import subprocess,sys,json,os
code=r'''
import json,sys
import pipeline.profile as p
out={}
for k in dir(p):
    if k.startswith('_'): continue
    v=getattr(p,k)
    if isinstance(v,(bool,int,float,str,type(None))): out[k]=v
    elif isinstance(v,(tuple,list,dict)):
        try: out[k]=json.loads(json.dumps(v,default=str))
        except Exception: out[k]=str(v)
print(json.dumps(out,sort_keys=True,default=str))
'''
def dump(name):
    env=dict(os.environ,VRP_PROFILE=name,PYTHONDONTWRITEBYTECODE='1')
    r=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True,env=env)
    if r.returncode!=0:
        print('ERROR',name,r.stderr[-400:]); sys.exit(1)
    return json.loads(r.stdout.strip().splitlines()[-1])
P=dump('mirova_equivalent')
for other in ['_s154_reproc_k_historico','experimental']:
    O=dump(other)
    diff=[k for k in sorted(set(P)|set(O)) if P.get(k)!=O.get(k)]
    print(f'== mirova_equivalent vs {other}: {len(diff)} diferencias de {len(set(P)|set(O))} claves')
    for k in diff: print('  ',k,'| prod:',str(P.get(k))[:60],'| otro:',str(O.get(k))[:60])
