# -*- coding: utf-8 -*-
"""Frente G S149: compara el TEXTO de los helpers JS duplicados entre las vistas.

Preguntas del instrumento:
1. Si las copias divergieran, esta medicion lo veria? Si: compara el cuerpo (sin comentarios ni
   espacios) funcion por funcion. NO ve diferencias de comportamiento que vengan del CALLER
   (con que innerKm se llama, que filtros se aplican antes): eso se lee aparte.
2. Si el instrumento estuviera muerto (extractor no encuentra nada), reporta AUSENTE, no IGUAL.
Control positivo: mirovaEqVrp de diario.html tiene otra firma (r, volcanoName): debe dar DISTINTO.
Solo lectura.
"""
import io, re, sys, hashlib, difflib, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[3] / "frontend"
VISTAS = ["index.html", "diario.html", "mosaico.html", "comparacion.html"]
FUNCS = ["mirovaEqVrp", "f5CoreMagnitude", "mirovaEqVrpCore", "mirovaEqVrpDisplay",
         "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact",
         "isValidDetection", "isSummitDetection", "esValorCensurado", "_havKm",
         "parseUtcMs", "ourSensorBucket", "isSensorVisible"]


def extraer(src, nombre):
    m = re.search(r"function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        return None
    i = src.index("{", src.index(")", m.end()))  # ojo: defaults sin llaves
    prof, j = 0, i
    while j < len(src):
        c = src[j]
        if c == "{":
            prof += 1
        elif c == "}":
            prof -= 1
            if prof == 0:
                break
        j += 1
    return src[m.start():j + 1]


def normalizar(t):
    t = re.sub(r"//[^\n]*", "", t)
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"\s+", "", t)


srcs = {v: (ROOT / v).read_text(encoding="utf-8") for v in VISTAS}
for f in FUNCS:
    cuerpos = {v: extraer(s, f) for v, s in srcs.items()}
    hs = {v: (hashlib.md5(normalizar(c).encode()).hexdigest()[:8] if c else "AUSENTE")
          for v, c in cuerpos.items()}
    presentes = {h for h in hs.values() if h != "AUSENTE"}
    estado = "IGUAL" if len(presentes) == 1 else ("DISTINTO" if presentes else "NO EXISTE")
    print(f"{f:26s} {estado:9s} " + "  ".join(f"{v.split('.')[0]}={h}" for v, h in hs.items()))
    if estado == "DISTINTO" and "--diff" in sys.argv:
        ref = "index.html"
        for v, c in cuerpos.items():
            if v != ref and c and cuerpos[ref] and hs[v] != hs[ref]:
                a = [l.strip() for l in re.sub(r"//[^\n]*", "", cuerpos[ref]).splitlines() if l.strip()]
                b = [l.strip() for l in re.sub(r"//[^\n]*", "", c).splitlines() if l.strip()]
                print(f"  --- index vs {v}")
                for l in difflib.unified_diff(a, b, lineterm="", n=0):
                    if not l.startswith(("---", "+++", "@@")):
                        print("   ", l)
