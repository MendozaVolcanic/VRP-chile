# -*- coding: utf-8 -*-
"""VAD2-05: separar_resultados con dos carpetas de artefactos que se llaman igual (corrida original y relanzamiento con
SOLO, ambas bajadas a '<algo>/artefactos'). El separador escribe dest/<parte>/<nombre de la carpeta>/<ruta relativa>:
si el nombre y la ruta relativa coinciden, la segunda pisa a la primera. Control positivo: con nombres distintos se
conservan las dos. Pregunta 1: si el separador perdiera resultados, esto lo veria? Si (cuenta ids antes y despues)."""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import *

base = TMP / "t4"
if base.exists():
    shutil.rmtree(base)
def res(i, estado="ok"):
    return {"id": i, "volcan": "Lascar", "hora_utc": "2026-05-01 05:00", "estado": estado}
# corrida original: ids 0,1 ok y 2 con error; relanzamiento SOLO: id 2 ok
for nombre, carpeta, filas in (("run1", "uno/artefactos", [res(0), res(1), res(2, "error: x")]),
                               ("run2", "dos/artefactos", [res(2)]),
                               ("run1b", "uno/arte_a", [res(0), res(1), res(2, "error: x")]),
                               ("run2b", "dos/arte_b", [res(2)])):
    d = base / carpeta / "s162-v750b-chunk-3"
    d.mkdir(parents=True)
    (d / "resultados_03.json").write_text(json.dumps(filas), encoding="utf-8")
for etiqueta, arts in (("MISMO NOMBRE", [base / "uno/artefactos", base / "dos/artefactos"]),
                       ("NOMBRES DISTINTOS", [base / "uno/arte_a", base / "dos/arte_b"])):
    dest = base / ("salida_" + etiqueta.replace(" ", "_"))
    rc, out = correr([sys.executable, ADENDA2 / "separar_resultados_v750b.py", "--art", *arts, "--dest", dest])
    ids = sorted(r["id"] + (0 if r["estado"] == "ok" else 1000) for f in (dest / "sellado").rglob("resultados_*.json")
                 for r in json.loads(f.read_text(encoding="utf-8")))
    print(f"{etiqueta}: rc={rc} | {out.strip()[:90]} | ids (estado ok = id, con error = id+1000) que quedan en sellado/: {ids}")
