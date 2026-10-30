# -*- coding: utf-8 -*-
"""VF P1-11: leer_equivalencia_local de evaluar_v750a.py (texto literal via ast) sobre (1) un archivo escrito a mano,
sin modulo, sin commit; (2) control negativo: la salida real del repo (linea base ROJA) tiene que dar False;
(3) control: el archivo escrito a mano sin la linea VERDE tiene que dar False.
Pregunta 1: si la lectura no atara el archivo al modulo, (1) daria True. Pregunta 2: si la funcion estuviera muerta
(siempre False o siempre True), (1) y (2) darian lo mismo."""
import sys, ast, re, pathlib, tempfile
sys.stdout.reconfigure(encoding="utf-8")
ev = pathlib.Path(sys.argv[1]); real = pathlib.Path(sys.argv[2])
src = ev.read_text(encoding="utf-8"); t = ast.parse(src)
ns = {"re": re, "Path": pathlib.Path}
for n in t.body:
    if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id in ("MIN_MUT_LOCAL", "MUT_LOCAL", "MIN_CASOS_LOCAL") for x in n.targets):
        exec(ast.get_source_segment(src, n), ns)
    if isinstance(n, ast.FunctionDef) and n.name == "leer_equivalencia_local":
        exec(ast.get_source_segment(src, n), ns)
f = ns["leer_equivalencia_local"]
falso = "\n".join(["VERDE: E1 1020 casos, E3 10 recortes"] +
                  [f"   mutación {m:20s} atrapada por aserción (x)" for m in ns["MUT_LOCAL"]] +
                  ["   mutación control_que_se_cae   caída (RuntimeError)", "mutaciones: TODAS COMO SE ESPERA"]) + "\n"
d = pathlib.Path(tempfile.mkdtemp(dir="."))
(d / "forjado.txt").write_text(falso, encoding="utf-8")
(d / "forjado_sin_verde.txt").write_text(falso.split("\n", 1)[1], encoding="utf-8")
print("(1) escrito a mano, sin modulo ni commit:", f(str(d / "forjado.txt")))
print("(2) control: salida real del repo (linea base ROJA):", f(str(real)))
print("(3) control: escrito a mano sin la linea VERDE:", f(str(d / "forjado_sin_verde.txt"))[0])
print("contenido del forjado:\n" + falso)
