"""Frente G: para cada atributo de pipeline.profile, donde se LEE en pipeline/ scripts/ (frontera de palabra).
Solo lectura. Salida: usos_atributos.json"""
import json, os, re, glob
here = os.path.dirname(__file__); root = os.path.abspath(os.path.join(here, "..", "..", ".."))
attrs = json.load(open(os.path.join(here, "perfil_efectivo.json"), encoding="utf-8"))
files = glob.glob(os.path.join(root, "pipeline", "*.py")) + glob.glob(os.path.join(root, "scripts", "*.py"))
src = {f: open(f, encoding="utf-8", errors="replace").read().splitlines() for f in files}
out = {}
for a in attrs:
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(a) + r"(?![A-Za-z0-9_])")
    hits = []
    for f, lines in src.items():
        rel = os.path.relpath(f, root).replace("\\", "/")
        for i, l in enumerate(lines, 1):
            if pat.search(l) and not l.lstrip().startswith("#"):
                hits.append(f"{rel}:{i}")
    out[a] = hits
json.dump(out, open(os.path.join(here, "usos_atributos.json"), "w"), indent=1)
for a, h in out.items():
    fuera = [x for x in h if not x.startswith("pipeline/profile.py")]
    print(a, len(fuera), " ".join(fuera[:8]))
