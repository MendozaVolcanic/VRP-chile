# Verificador adenda K, pregunta 1: resuelve las constantes de pipeline.profile en UN PROCESO LIMPIO POR PERFIL
# (la prueba del PR #856 usa importlib.reload en un solo proceso) y compara produccion, control K y diurno K.
# Ademas compara contra los brazos C0 (_s151_ab_diurno_*) para mostrar que el instrumento ve las diferencias de K.
import json, os, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
COD = "import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) if k.isupper()}))"
def res(n):
    r = subprocess.run([sys.executable, "-c", COD], cwd=RAIZ, capture_output=True, text=True, check=True,
                       env=dict(os.environ, VRP_PROFILE=n, PYTHONIOENCODING="utf-8"))
    return json.loads([l for l in r.stdout.splitlines() if l.startswith("@@")][0][2:])
P = {n: res(n) for n in ("mirova_equivalent", "_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on",
                         "_s151_ab_diurno_control", "_s151_ab_diurno_on")}
dif = lambda a, b: sorted(k for k in set(P[a]) | set(P[b]) if P[a].get(k) != P[b].get(k))
print("constantes en produccion:", len(P["mirova_equivalent"]))
for a, b in (("mirova_equivalent", "_s154_ab_diurno_k_control"), ("_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on"),
             ("_s154_ab_diurno_k_control", "_s151_ab_diurno_control"), ("_s154_ab_diurno_k_on", "_s151_ab_diurno_on")):
    print("%s vs %s: %s" % (a, b, dif(a, b)))
