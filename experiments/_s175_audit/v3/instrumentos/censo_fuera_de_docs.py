# Q1: si el censo S145 SI cubriera los cierres de S160+, los documentos fuera de censo.DOCS donde nacen darian 0 coincidencias; si dan >0, el censo no los ve. Q2: instrumento muerto => control positivo [] (se imprime).
# Detectores: censo.py de 752d348bc (v3/censo_752.py). Ventana: 395af8034 (rama loop/activo) para tasks/; 752d348bc para docs/. Denominador: lineas de cada archivo.
import importlib.util, subprocess, sys, re
from pathlib import Path
spec = importlib.util.spec_from_file_location("censo", Path(sys.argv[1])); c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
cwd = sys.argv[2]
print("control positivo:", c.tipos_de_cierre("queda CERRADA, no reabrir"), "| DOCS del censo:", c.DOCS)
def lst(commit, pref):
    return subprocess.run(["git","ls-tree","-r","--name-only",commit],capture_output=True,text=True,cwd=cwd).stdout.split()
def cuenta(commit, rel):
    r = subprocess.run(["git","show",f"{commit}:{rel}"],capture_output=True,cwd=cwd)
    ls = r.stdout.decode("utf-8","replace").split("\n")
    hits=[(i+1,c.tipos_de_cierre(l)) for i,l in enumerate(ls) if c.tipos_de_cierre(l)]
    return len(ls), hits
tot=0
for commit, pats in (("395af8034",[r"^tasks/LOOP_OBJETIVOS\.md$", r"^tasks/BLOQUE_ARRANQUE_S1(6\d|7\d)\.md$"]), ("752d348bc",[r"^docs/AUDIT_S1[5-9]\d\.md$", r"^docs/SINTOMAS\.md$"])):
    for rel in lst(commit,""):
        if any(re.search(p,rel) for p in pats):
            n,h = cuenta(commit, rel); tot+=len(h)
            if h: print(f"{commit[:9]} {rel}: lineas={n} coincidencias={len(h)}")
print("TOTAL coincidencias fuera de censo.DOCS:", tot)
