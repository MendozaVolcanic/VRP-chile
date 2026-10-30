# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding="utf-8")
"""VF P1-01: el predicado y los inner del tablero, en el worktree (01ffd277b) contra main (443da8649, cc3887290) y el
tag sellado. Pregunta 1: si el tablero del worktree difiriera en el predicado, esta medicion lo veria (compara el texto
exacto de cada funcion que banco_paridad._JS extrae, y los inner). Pregunta 2: control positivo: el texto completo de
index.html difiere entre commits (si saliera igual, el extractor estaria muerto)."""
import hashlib, re, subprocess, sys, os
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
FUN = ['_havKm','mirovaEqVrp','f5CoreMagnitude','mirovaEqVrpCore','mirovaEqVrpDisplay','isCirrusArtifact',
       'isDiffuseFieldArtifact','isThermalArtifact','isValidDetection','isSummitDetection']
VOLS = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica",
        "Copahue","PuyehueCordonCaulle","Chaiten"]
def show(c, f):
    return subprocess.run(["git","-C",REPO,"show",f"{c}:{f}"],capture_output=True,env={**os.environ,"MSYS_NO_PATHCONV":"1"}).stdout.decode("utf-8")
def extraer(src, n):
    i = src.find('function ' + n + '(')
    if i < 0: return None
    j = src.find('{', i); d = 0
    for k in range(j, len(src)):
        if src[k] == '{': d += 1
        elif src[k] == '}':
            d -= 1
            if d == 0: return src[i:k+1]
def const(src, n):
    m = re.search('const ' + n + r'\s*=\s*([^;]+);', src); return m.group(0) if m else None
def inner(src):
    out = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', src):
        out.setdefault(m.group(1), float(m.group(2)))
    return {v: out.get(v) for v in VOLS}
COMMITS = ["01ffd277b","s162-v750b-sellado","443da8649","cc3887290"]
data = {}
for c in COMMITS:
    s = show(c, "frontend/index.html")
    data[c] = dict(full=hashlib.sha256(s.encode()).hexdigest()[:12],
                   fun={n: hashlib.sha256((extraer(s,n) or "AUSENTE").encode()).hexdigest()[:12] for n in FUN},
                   const={n: const(s,n) for n in ("F5_R_CORE_KM","F5_BT_EXT_K")}, inner=inner(s), src=s)
    print(c, "index.html", data[c]["full"], "bytes", len(s))
base = "01ffd277b"
for c in COMMITS[1:]:
    print(f"\n== {base} contra {c}")
    print("  index.html completo igual:", data[base]["full"] == data[c]["full"], "(control positivo: main tiene que diferir)")
    print("  funciones del predicado distintas:", [n for n in FUN if data[base]["fun"][n] != data[c]["fun"][n]] or "ninguna")
    print("  constantes:", "iguales" if data[base]["const"] == data[c]["const"] else (data[base]["const"], data[c]["const"]))
    print("  inner distintos:", {v: (data[base]["inner"][v], data[c]["inner"][v]) for v in VOLS if data[base]["inner"][v] != data[c]["inner"][v]} or "ninguno")
# donde difieren (lineas del diff)
import difflib
d = list(difflib.unified_diff(data[base]["src"].splitlines(), data["443da8649"]["src"].splitlines(), lineterm="", n=0))
print("\n== diff 01ffd277b -> 443da8649: lineas cambiadas", sum(1 for x in d if x[:1] in "+-" and x[:3] not in ("+++","---")))
for x in d[:60]: print("  ", x[:200])
