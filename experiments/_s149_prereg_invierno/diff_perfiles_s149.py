# -*- coding: utf-8 -*-
"""S149. Resuelve cada perfil COMO LO RESUELVE EL CODIGO (subproceso con VRP_PROFILE, A89) y lista en que
atributos difieren los pares control/brazo del pre-registro de invierno."""
import json, os, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
COD = "import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) if k.isupper() and k != 'VALID_PROFILES'}))"
def resolver(nombre):
    out = subprocess.run([sys.executable, "-c", COD], capture_output=True, text=True, cwd=RAIZ, env=dict(os.environ, VRP_PROFILE=nombre, PYTHONIOENCODING="utf-8")).stdout
    return json.loads([l for l in out.splitlines() if l.startswith("@@")][0][2:])
for a, b in (("_s146_ab_sin_test1", "_s149_ab_sin_test1_gemelo"), ("_s146_ab_sin_test1", "_s149_ab_sin_test1_b22"), ("_s149_ab_sin_test1_b22", "_s149_ab_sin_test1_b22_max"), ("_s146_ab_sin_test1", "_s147_ab_sin_test1_max")):
    A, B = resolver(a), resolver(b)
    d = sorted(k for k in set(A) | set(B) if A.get(k) != B.get(k))
    print("%s -> %s | atributos %d | difieren %d:" % (a, b, len(A), len(d)))
    for k in d: print("     %-36s %s -> %s" % (k, A.get(k), B.get(k)))
