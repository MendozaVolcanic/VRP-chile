"""Resuelve cada perfil de pipeline/profiles/ como lo resuelve el codigo (VRP_PROFILE + pipeline.profile, A89)
y clasifica su detector: K (los tres flags de K), C0 (los tres de C0) u OTRO. Marca los perfiles cuyo texto dice
'idéntico al operacional' / 'IGUAL al operacional'.
P1: un perfil que no resuelve sale como ERROR, no como C0.
P2: control positivo: mirova_equivalent debe salir K y experimental C0 (leidos aparte en leer_flags.out)."""
import os, sys, subprocess, json, glob, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
code = ("import json,pipeline.profile as p;print('JSON'+json.dumps([p.ENABLE_TEST1_PATH,p.ENABLE_TESTS_23_PROSE_BRANCH,p.ENABLE_MODIS_B22_PRIMARY]))")
res = {}
for f in sorted(glob.glob("pipeline/profiles/*.yaml")):
    name = os.path.basename(f)[:-5]
    env = dict(os.environ, VRP_PROFILE=name, PYTHONPATH=".")
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    m = [l for l in out.stdout.splitlines() if l.startswith("JSON")]
    if not m:
        res[name] = "ERROR"; continue
    t1, prose, b22 = json.loads(m[0][4:])
    res[name] = "K" if (not t1 and prose and b22) else ("C0" if (t1 and not prose and not b22) else f"OTRO(t1={t1},max={prose},b22={b22})")
txt_ident = {}
for f in glob.glob("pipeline/profiles/*.yaml"):
    s = open(f, encoding="utf-8").read()
    if re.search(r"id[eé]ntico al operacional|IGUAL al operacional", s, re.I):
        txt_ident[os.path.basename(f)[:-5]] = True
from collections import Counter
print("conteo por detector:", Counter(v if not v.startswith("OTRO") else "OTRO" for v in res.values()), "de", len(res))
for n, v in res.items():
    if v.startswith("OTRO") or v == "ERROR" or n in txt_ident or n in ("mirova_equivalent", "experimental"):
        print(f"{n:55s} {v:28s} {'DICE idéntico/IGUAL al operacional' if n in txt_ident else ''}")
