"""Frente G: extrae las funciones del predicado de las 3 vistas y las compara tras quitar comentarios y espacios.
Solo lectura."""
import re, os, json, hashlib, difflib
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FUNCS = ["getLevel","mirovaEqVrp","f5CoreMagnitude","mirovaEqVrpCore","mirovaEqVrpDisplay","eqVrpDisplay",
         "isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","isValidDetection","isSummitDetection",
         "latestDetection","latestVRP","_havKm"]
def extraer(src, name):
    m = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    if not m: return None
    i = src.index("{", src.index(")", m.end()) if False else m.end())
    # avanzar hasta la llave que abre el cuerpo: saltar parentesis de parametros
    depth = 0; j = m.end() - 1
    while True:
        c = src[j]
        if c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0: break
        j += 1
    i = src.index("{", j); depth = 0; k = i
    while True:
        c = src[k]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: break
        k += 1
    return src[m.start():k+1], src[:m.start()].count("\n") + 1
def norm(t):
    t = re.sub(r"//[^\n]*", "", t); t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"\s+", "", t)
res = {}
srcs = {f: open(os.path.join(root, "frontend", f + ".html"), encoding="utf-8").read() for f in ("index","diario","mosaico","comparacion")}
for fn in FUNCS:
    res[fn] = {}
    for f, s in srcs.items():
        e = extraer(s, fn)
        res[fn][f] = None if e is None else {"linea": e[1], "sha": hashlib.sha1(norm(e[0]).encode()).hexdigest()[:10], "norm": norm(e[0])}
for fn, d in res.items():
    print(fn, {f: (v["linea"], v["sha"]) if v else None for f, v in d.items()})
# LEVELS y constantes
for f, s in srcs.items():
    lv = re.findall(r'key:\s*"(\w+)",\s*label:\s*"([^"]+)",\s*max:\s*(\w+)', s)
    print(f, "LEVELS", lv)
    print(f, "INNER default", re.findall(r"inner_radius_km\s*\?\?\s*(\d+)|INNER_RADIUS_KM\[\w+\]\s*\?\?\s*(\d+)", s)[:6])
for fn in ("mirovaEqVrp","mirovaEqVrpCore","isCirrusArtifact","isValidDetection","isSummitDetection","latestVRP"):
    for f in ("diario","mosaico"):
        a, b = res[fn]["index"], res[fn][f]
        if a and b and a["sha"] != b["sha"]:
            print("\n### DIFERENCIA", fn, "index vs", f)
            print("index :", a["norm"][:900]); print(f, ":", b["norm"][:900])
json.dump({fn: {f: ({"linea": v["linea"], "sha": v["sha"]} if v else None) for f, v in d.items()} for fn, d in res.items()},
          open(os.path.join(os.path.dirname(__file__), "frontend_funciones.json"), "w"), indent=1)
