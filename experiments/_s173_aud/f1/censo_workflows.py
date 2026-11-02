# -*- coding: utf-8 -*-
"""Workflows que corren un perfil: cual, si la via de MODIS queda encendida (resuelta con pipeline.profile en
perfiles_<X>.tsv), si instalan pyproj en una linea pip no comentada, y como se disparan.

Preguntas del instrumento:
1. Si un workflow corriera produccion sin pyproj, ¿se veria? Si: control positivo = nrt.yml en la base (sin el PR A)
   tiene que salir SIN pyproj; se mide aparte con `git show a3c5a9b49:.github/workflows/nrt.yml`.
2. Si el parser estuviera muerto, ¿se veria? Si: un workflow sin perfil detectado sale con perfiles vacios, y nrt.yml
   tiene que traer mirova_equivalent.
Uso: python censo_workflows.py <worktree> <perfiles.tsv> <salida.tsv> [ruta_workflows_alternativa]
"""
import re
import sys
from pathlib import Path

WT = Path(sys.argv[1])
PERF = {}
for ln in open(sys.argv[2], encoding="utf-8").read().splitlines()[1:]:
    c = ln.split("\t")
    PERF[c[0]] = (c[3], c[4])
OUT = sys.argv[3]
WFD = Path(sys.argv[4]) if len(sys.argv) > 4 else WT / ".github" / "workflows"

def sin_comentarios(t):
    return "\n".join(ln.split(" #")[0] for ln in t.splitlines() if not ln.lstrip().startswith("#"))

filas = []
for wf in sorted(WFD.glob("*.yml")):
    t = sin_comentarios(wf.read_text(encoding="utf-8", errors="replace"))
    perfiles = set()
    for m in re.finditer(r"(?:VRP_PROFILE[=: ]+|--profile[= ]+|profile:\s*)[\"']?([A-Za-z0-9_\-\$\{\}\.]+)", t):
        perfiles.add(m.group(1))
    # perfiles en listas de matrix u opciones de input
    for name in PERF:
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", t):
            perfiles.add(name)
    perfiles = {p for p in perfiles if p in PERF or "$" in p}
    if not perfiles and "run_pipeline" not in t:
        continue
    pip = [ln.strip() for ln in t.splitlines() if "pip install" in ln]
    pyproj = any("pyproj" in ln for ln in pip) or "requirements" in " ".join(pip)
    req = any("requirements" in ln for ln in pip)
    trig = []
    if re.search(r"^\s*schedule:", t, re.M):
        trig.append("schedule")
    if "workflow_dispatch" in t:
        trig.append("dispatch")
    if "workflow_run" in t:
        trig.append("workflow_run")
    if re.search(r"^\s*push:", t, re.M):
        trig.append("push")
    con_via = sorted(p for p in perfiles if PERF.get(p, ("", ""))[0] == "True")
    con_via_modis = sorted(p for p in perfiles if PERF.get(p) == ("True", "True"))
    filas.append((wf.name, ",".join(trig), ",".join(sorted(perfiles)), ",".join(con_via_modis),
                  "si" if any("pyproj" in ln for ln in pip) else ("requirements" if req else "NO"),
                  "run_pipeline" if "run_pipeline" in t else ""))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("workflow\tdisparo\tperfiles\tperfiles_con_via_y_MODIS\tpyproj\tcorre\n")
    for f in filas:
        fh.write("\t".join(f) + "\n")
mal = [f for f in filas if f[3] and f[4] == "NO"]
print(f"workflows_con_perfil={len(filas)} con_via_MODIS={sum(1 for f in filas if f[3])} via_sin_pyproj={len(mal)}")
for f in mal:
    print("  SIN pyproj:", f[0], f[1], f[3])
nrt = next((f for f in filas if f[0] == "nrt.yml"), None)
print("control nrt.yml:", nrt)
