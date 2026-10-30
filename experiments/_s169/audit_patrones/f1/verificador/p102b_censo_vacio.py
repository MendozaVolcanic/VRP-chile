# -*- coding: utf-8 -*-
"""VF P1-02 (b): ¿una ruta de --censo-art que no existe da FALLA o error? cargar() del analizador, texto literal.
Control positivo: una carpeta con un resultados_x.json con 1 pasada ok carga 1."""
import sys, json, tempfile, pathlib, ast
sys.stdout.reconfigure(encoding="utf-8")
src = open(sys.argv[1], encoding="utf-8").read()
t = ast.parse(src); f = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == "cargar"][0]
ns = {"Path": pathlib.Path, "json": json}; exec(ast.get_source_segment(src, f), ns)
print("ruta inexistente ->", len(ns["cargar"](["D:/no/existe/censo_xxx"])), "pasadas (sin excepcion)")
d = tempfile.mkdtemp(dir=".")
pathlib.Path(d, "resultados_1.json").write_text(json.dumps([{"id": 7, "estado": "ok"}]), encoding="utf-8")
print("control positivo ->", len(ns["cargar"]([d])), "pasada")
print("=> con 0 pasadas comunes, cnt queda vacio y censo_ok = bool(cnt) = False: se imprime '{} FALLA', igual palabra que DISTINTO")
