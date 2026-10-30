# P1: si el manifiesto omitiera un modulo que el arnes usa en tiempo de ejecucion, lo veria? Si: importo lo que importan main() de probe_f4 e identidad_f4.contexto
#     (run_pipeline y pipeline.fetch) y comparo los archivos cargados contra el manifiesto.
# P2: control positivo: el conjunto de modulos que SI esta en el manifiesto (probe_f4/evaluar_f4 al importar) debe estar incluido (si no, mi medicion esta mal).
import sys, os, json, subprocess
R='D:/vrp-trabajo/temporales/s169_ver_candado/arbol'
code = r'''
import sys, os, json
os.environ.setdefault("VRP_PROFILE","mirova_equivalent")
A=sys.argv[1]; R=sys.argv[2]
sys.path.insert(0,R); sys.path.insert(0,R+"/scripts"); sys.path.insert(0,A)
import probe_f4, evaluar_f4, identidad_f4
base={os.path.abspath(m.__file__) for m in list(sys.modules.values()) if getattr(m,"__file__",None) and os.path.abspath(m.__file__).startswith(os.path.abspath(R))}
import run_pipeline as rp
from pipeline.fetch import auth, download_granules
rp.load_volcanoes("Lascar")
lazy={os.path.abspath(m.__file__) for m in list(sys.modules.values()) if getattr(m,"__file__",None) and os.path.abspath(m.__file__).startswith(os.path.abspath(R))}
print(json.dumps({"base":sorted(base),"lazy":sorted(lazy)}))
'''
env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
r=subprocess.run([sys.executable,'-I','-c',code,R+'/experiments/_s166_modd_f4',R],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
d=json.loads(r.stdout.strip().splitlines()[-1])
m=json.load(open(R+'/experiments/_s166_modd_f4/MANIFIESTO_CANDADO_F4.json',encoding='utf-8'))['archivos']
rel=lambda L: sorted({os.path.relpath(x,R).replace(chr(92),'/') for x in L if '__pycache__' not in x})
base, lazy = rel(d['base']), rel(d['lazy'])
print('base (import de probe/evaluar/identidad):', len(base), 'fuera del manifiesto:', [x for x in base if x not in m and x.split('/')[0] in ('experiments','scripts','pipeline')])
print('tras usar run_pipeline + pipeline.fetch:', len(lazy), 'fuera del manifiesto:', [x for x in lazy if x not in m and x.split('/')[0] in ('experiments','scripts','pipeline')])
# archivos de datos que lee run_pipeline.load_volcanoes
print('volcanic_features.yaml en manifiesto:', 'pipeline/volcanic_features.yaml' in m, '| volcanoes.yaml:', 'volcanoes.yaml' in m)
