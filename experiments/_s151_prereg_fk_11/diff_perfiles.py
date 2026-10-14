# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Resuelve cada perfil del A/B COMO LO RESUELVE EL CODIGO (subproceso con VRP_PROFILE,
A89: nunca leyendo el YAML) y lista en que atributos difieren los pares. Copia de
experiments/_s150_ndc/diff_perfiles_ndc.py con los pares de este pre-registro, mas la linea FLAGS_BRAZO que
cada brazo deberia escribir en su log (la misma lista de claves que el workflow imprime).

  python diff_perfiles.py > diff_perfiles_salida.txt
"""
import io, json, os, subprocess, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
COD = "import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) if k.isupper() and k != 'VALID_PROFILES'}))"
FLAGS = ("PROFILE_NAME", "DATA_SUBDIR", "ENABLE_TEST1_PATH", "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY",
         "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER", "PATH_D_ONLY_CAP_MW", "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375",
         "ENABLE_VENT_ANCHORED_CLUSTERING")


def resolver(nombre):
    out = subprocess.run([sys.executable, "-c", COD], capture_output=True, text=True, cwd=RAIZ,
                         env=dict(os.environ, VRP_PROFILE=nombre, PYTHONIOENCODING="utf-8")).stdout
    return json.loads([l for l in out.splitlines() if l.startswith("@@")][0][2:])


PARES = (("mirova_equivalent", "_s146_ab_control"), ("_s146_ab_control", "_s151_ab_control_gemelo"),
         ("_s146_ab_control", "_s147_ab_sin_test1_max"), ("_s146_ab_control", "_s149_ab_sin_test1_b22_max"),
         ("_s147_ab_sin_test1_max", "_s149_ab_sin_test1_b22_max"))
cache = {}
for a, b in PARES:
    A = cache.setdefault(a, resolver(a)); B = cache.setdefault(b, resolver(b))
    d = sorted(k for k in set(A) | set(B) if A.get(k) != B.get(k))
    print("%s -> %s | atributos %d | difieren %d:" % (a, b, len(A), len(d)))
    for k in d:
        print("     %-36s %s -> %s" % (k, A.get(k), B.get(k)))
print("\nFLAGS_BRAZO esperada por brazo (valores que el codigo resuelve hoy):")
for n in ("_s146_ab_control", "_s151_ab_control_gemelo", "_s147_ab_sin_test1_max", "_s149_ab_sin_test1_b22_max"):
    print("   %-28s %s" % (n, {k: cache[n].get(k) for k in FLAGS}))
