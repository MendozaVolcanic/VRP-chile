# -*- coding: utf-8 -*-
"""S127 — capacidad construida, testeada y nunca conectada al pipeline.

POR QUE: `pipeline/geo_utils.py` define `get_grid_center()` desde S98 justamente para
devolver el centro de grilla de MIROVA, con la prioridad `mirova_center -> vent -> lat/lon`.
Tiene tests. Y en produccion NO LA LLAMA NADIE — el regrid se sigue centrando en
`volcano["lat"]/["lon"]` (`process_modis.py:455`). Es la instancia #11 de la lista de S126
y el cabo suelto que sostiene D17.

Una funcion dormida es peor que una ausente: aparece en las busquedas, tiene tests verdes,
y cualquiera que lea el modulo concluye que el comportamiento esta implementado. Cuando la
auditoria S114 dio por agotado el eje espacial, esta funcion ya llevaba 16 sesiones escrita
sin uso — y A82 tuvo que ser REBAJADA en S125 justamente porque nadie habia mirado la
geometria.

Que cuenta como "conectada": que la llame algun modulo de `pipeline/` o `scripts/`. Los
tests NO cuentan (un test que ejercita una funcion muerta prueba que la funcion anda, no
que el sistema la use), y `experiments/` tampoco (un probe offline no es produccion).

Persiste en 04_capacidad_dormida.json.
"""
import ast
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

PRODUCCION = (sorted(glob.glob(os.path.join(ROOT, "pipeline", "*.py")))
              + sorted(glob.glob(os.path.join(ROOT, "scripts", "*.py"))))

# Puntos de entrada y convenciones que no se llaman desde otro modulo.
EXENTAS = {"main", "run", "__init__"}


def _publicas(path):
    """Funciones publicas definidas a nivel de modulo."""
    try:
        arbol = ast.parse(io.open(path, encoding="utf-8").read())
    except SyntaxError:
        return []
    return [n.name for n in arbol.body
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]


fuentes = {p: io.open(p, encoding="utf-8", errors="replace").read()
           for p in PRODUCCION}

dormidas = []
alias_de = {}
for path in PRODUCCION:
    modulo = os.path.relpath(path, ROOT).replace("\\", "/")
    for fn in _publicas(path):
        if fn in EXENTAS:
            continue
        # OJO: hay que contar tambien las llamadas CALIFICADAS (`store.append_record(`,
        # `fetch.auth(`). La primera version de este barrido excluia el punto previo y
        # daba `append_record` y `auth` como dormidas cuando run_pipeline.py las llama
        # todo el tiempo. Mismo error de forma que buscar el nombre del parametro en vez
        # del de la clave (A48): no falla, devuelve cero y el cero se lee como ausencia.
        pat = re.compile(r"(?<![\w])(?:[\w]+\.)?%s\s*\(" % re.escape(fn))
        llamadas = collections.Counter()
        for p2, src in fuentes.items():
            n = len(pat.findall(src))
            if p2 == path:
                n -= 1 if re.search(r"^\s*def\s+%s\s*\(" % re.escape(fn), src, re.M) else 0
            if n > 0:
                llamadas[os.path.relpath(p2, ROOT).replace("\\", "/")] = n
        # una funcion llamada SOLO por su propio modulo puede ser un alias:
        # lo anotamos aparte porque el alias puede estar dormido tambien.
        externas = {k: v for k, v in llamadas.items() if k != modulo}
        if not externas:
            solo_propia = llamadas.get(modulo, 0)
            dormidas.append({"modulo": modulo, "funcion": fn,
                             "llamadas_en_su_propio_modulo": solo_propia})

print("CAPACIDAD DORMIDA — funciones publicas de produccion sin call site externo")
print("=" * 88)
print("%-34s %-30s %s" % ("modulo", "funcion", "llamadas en su propio modulo"))
print("-" * 88)
por_modulo = collections.Counter()
for d in dormidas:
    por_modulo[d["modulo"]] += 1
    print("%-34s %-30s %d"
          % (d["modulo"][:34], d["funcion"][:30], d["llamadas_en_su_propio_modulo"]))
if not dormidas:
    print("  ninguna")

print("\nresumen: %d funciones dormidas en %d modulos" % (len(dormidas), len(por_modulo)))

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "04_capacidad_dormida.json")
json.dump({"total": len(dormidas), "dormidas": dormidas},
          io.open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("persistido en", os.path.relpath(dest, ROOT).replace("\\", "/"))
