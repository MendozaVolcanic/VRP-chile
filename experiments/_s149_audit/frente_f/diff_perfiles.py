"""Frente F, S149. Compara los perfiles experimentales contra mirova_equivalent
tal como los resuelve pipeline.profile (regla A89: nunca leyendo el YAML).

Las dos preguntas del instrumento:
1. Si los perfiles difirieran, esto lo veria? Si: compara TODAS las constantes publicas
   en mayusculas del modulo. Control positivo: DATA_SUBDIR debe diferir siempre, y
   _s147_ab_sin_test1_max (brazo A/B conocido) debe mostrar diferencias de flags.
2. Si el instrumento estuviera muerto? Se imprime el numero de constantes comparadas;
   cero constantes = SIN DATO.
Solo lectura: importa el modulo en un subproceso por perfil.
"""
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

SNIPPET = (
    "import json, pipeline.profile as p;"
    "d={k:repr(getattr(p,k)) for k in dir(p) if k.isupper() and not k.startswith('_')};"
    "print(json.dumps(d))"
)


def resolver(nombre):
    env = dict(os.environ, VRP_PROFILE=nombre, PYTHONIOENCODING="utf-8")
    out = subprocess.run([sys.executable, "-c", SNIPPET], cwd=REPO, env=env,
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        print(f"[{nombre}] ERROR al resolver:\n{out.stderr[-800:]}")
        return None
    return json.loads(out.stdout.strip().splitlines()[-1])


base = resolver("mirova_equivalent")
print(f"mirova_equivalent: {len(base)} constantes resueltas")
IGNORAR = {"VALID_PROFILES"}
for nombre in ["experimental", "experimental_ndc_focus", "experimental_lowT",
               "_s147_ab_sin_test1_max"]:
    d = resolver(nombre)
    if d is None:
        continue
    claves = (set(base) | set(d)) - IGNORAR
    difs = sorted(k for k in claves if base.get(k) != d.get(k))
    print(f"\n=== {nombre}: {len(d)} constantes, {len(difs)} difieren del operacional ===")
    for k in difs:
        print(f"  {k}: operacional={base.get(k)}  |  {nombre}={d.get(k)}")
