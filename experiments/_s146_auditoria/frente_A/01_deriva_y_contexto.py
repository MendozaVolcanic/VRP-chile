# -*- coding: utf-8 -*-
"""S146 frente A, paso 1: comprueba que las 50 lineas del censo siguen donde el censo dice, y
vuelca el contexto amplio de cada una para leerlo.

Las dos preguntas del instrumento:
 1. Si lo que mide estuviera roto (las lineas se corrieron), esta prueba fallaria? SI: compara el
    texto guardado en el JSON del censo contra la linea actual del archivo y marca DERIVA; si no
    coincide busca el texto en todo el archivo y reporta la linea nueva.
 2. Si el instrumento estuviera muerto, el resultado se veria distinto? SI: si el JSON no carga o
    trae 0 filas sin respaldo, aborta con error en vez de imprimir "0 derivas".
Solo lee. Escribe el volcado fuera del repo (ruta pasada por argumento).
"""
import io, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
censo = json.loads((ROOT / "experiments/_s145_censo_cierres/censo_cierres.json").read_text(encoding="utf-8"))
filas = [f for f in censo["afirmaciones"] if f["sin_respaldo_citable"]]
assert len(filas) > 0, "instrumento muerto: 0 filas sin respaldo"
print("filas sin respaldo:", len(filas), "| generado:", censo["generado_utc"])
out = []
cache = {}
deriva = 0
for n, f in enumerate(filas, 1):
    L = cache.setdefault(f["archivo"], (ROOT / f["archivo"]).read_text(encoding="utf-8", errors="replace").split("\n"))
    i = f["linea"] - 1
    ok = i < len(L) and L[i].strip()[:300] == f["texto"]
    nueva = None
    if not ok:
        deriva += 1
        c = [k + 1 for k, l in enumerate(L) if l.strip()[:300] == f["texto"]]
        nueva = c
        print(f"DERIVA #{n} {f['archivo']}:{f['linea']} -> {c}")
        if len(c) == 1:
            i = c[0] - 1
    out.append(f"\n\n######## #{n} {f['archivo']}:{f['linea']} (actual {i+1}) tipos={f['tipos_de_cierre']} resp={f['respaldos_citados']}")
    for k in range(max(0, i - 10), min(len(L), i + 16)):
        out.append(f"{k+1:5}{'>>' if k == i else '  '} {L[k]}")
print("derivas:", deriva, "de", len(filas))
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text("\n".join(out), encoding="utf-8")
    print("volcado en", sys.argv[1])
