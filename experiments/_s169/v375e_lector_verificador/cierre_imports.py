# B7. Cierre de imports (estatico, AST) desde los puntos de entrada de la via VIIRS 375 y de K VIIRS 375.
# P1: si la via leyera un modulo que no aparece aqui, ¿se veria? NO si lo carga por importlib/ruta dinamica: lo cubro con grep de lecturas de archivo abajo.
# Control positivo: mirova_v750_codigo.py y grillas_mirova.yaml deben aparecer en el cierre.
import ast, sys, re
from pathlib import Path
R=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol")
def mods(py):
    t=ast.parse(py.read_text(encoding="utf-8")); out=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names: out.add(a.name)
        elif isinstance(n,ast.ImportFrom):
            b=("."*n.level)+(n.module or "")
            out.add(b)
            for a in n.names: out.add(b+"."+a.name if n.module else a.name)
    return out
def resolver(name, origen):
    n=name.lstrip(".")
    if name.startswith("."):
        base=origen.parent; cand=[base/(n.replace(".","/")+".py")]
    else:
        cand=[R/(n.replace(".","/")+".py"), R/"pipeline"/(n.replace(".","/")+".py")]
    return next((c for c in cand if c.exists()),None)
def cierre(entrada):
    vistos=set(); cola=[entrada]
    while cola:
        p=cola.pop()
        if p in vistos: continue
        vistos.add(p)
        for m in mods(p):
            if m.split(".")[0] in ("pipeline","scripts") or m.startswith(".") or (R/"pipeline"/(m+".py")).exists():
                c=resolver(m,p)
                if c and c.is_relative_to(R/"pipeline") or (c and c.is_relative_to(R/"scripts")): cola.append(c)
    return vistos
for ent in ("pipeline/process_viirs.py","pipeline/store.py","scripts/run_pipeline.py"):
    cs=sorted(str(p.relative_to(R)).replace("\\","/") for p in cierre(R/ent) if p.is_relative_to(R/"pipeline"))
    print("==",ent,"->",len(cs),"modulos de pipeline/:"); print("  "+", ".join(Path(c).name for c in cs))
allp={p.name for p in (R/"pipeline").glob("*.py")}
usados=set()
for ent in ("pipeline/process_viirs.py","pipeline/store.py","scripts/run_pipeline.py"):
    usados|={p.name for p in cierre(R/ent) if p.is_relative_to(R/"pipeline")}
print("\npipeline/*.py NO alcanzados por ninguna entrada (estaticamente):", sorted(allp-usados))
print("\nlecturas de archivos no-py en el cierre (yaml/json):")
for p in sorted({q for ent in ("pipeline/process_viirs.py","pipeline/store.py","scripts/run_pipeline.py") for q in cierre(R/ent)}):
    s=p.read_text(encoding="utf-8")
    for m in sorted(set(re.findall(r'["\']([\w./-]+\.(?:yaml|yml|json|csv))["\']',s))):
        print("  ",p.relative_to(R).as_posix(),"->",m)
