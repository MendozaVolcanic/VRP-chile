# -*- coding: utf-8 -*-
"""F4-06: diferencias efectivas entre perfiles, leidas desde pipeline.profile (A89), no del YAML.
P1: control positivo, DATA_SUBDIR debe diferir. P2: si el import fallara, el script aborta."""
import os, subprocess, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
code = "import json,pipeline.profile as p; print(json.dumps({k:repr(getattr(p,k)) for k in dir(p) if k.isupper()}))"
def leer(prof):
    o = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, VRP_PROFILE=prof), check=True)
    return json.loads(o.stdout.strip().splitlines()[-1])
a = leer("mirova_equivalent")
for prof in sys.argv[1:]:
    b = leer(prof)
    d = {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}
    print("==", prof, "difiere de mirova_equivalent en", len(d))
    for k, v in d.items(): print("  ", k, "op:", v[0], "| lab:", v[1])
