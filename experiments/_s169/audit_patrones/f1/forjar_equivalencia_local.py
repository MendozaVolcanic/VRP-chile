# Auditoría S169 f1 (P-C/P-B): ¿leer_equivalencia_local de evaluar_v750a.py (§6.1 parte local) acepta un archivo escrito
# a mano? Se extrae la función con ast (sin importar el evaluador entero) y se le da un archivo fabricado.
# Pregunta 1: si la compuerta local estuviera rota, ¿se vería? Control positivo: archivo ausente -> False; archivo con
# 'ROJA' -> False. Pregunta 2: el archivo forjado NO contiene ninguna corrida real.
import ast, re, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
src = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f1_v750/arbol/experiments/_s162_v750a/evaluar_v750a.py").read_text(encoding="utf-8")
t = ast.parse(src)
ns = {"re": re, "Path": Path}
for n in t.body:
    if isinstance(n, ast.Assign) and any(getattr(x, "id", "") in ("MIN_MUT_LOCAL", "MIN_CASOS_LOCAL", "MUT_LOCAL") for x in n.targets):
        exec(ast.get_source_segment(src, n), ns)
    if isinstance(n, ast.FunctionDef) and n.name == "leer_equivalencia_local":
        exec(ast.get_source_segment(src, n), ns)
f = ns["leer_equivalencia_local"]
print("MUT_LOCAL =", ns["MUT_LOCAL"])
d = Path(tempfile.mkdtemp(dir="D:/vrp-trabajo/temporales/s169_audit_patrones/f1_v750"))
forjado = "VERDE: E1 1020 casos, E3 10 recortes\n" + "".join(f"   mutación {m:20s} atrapada por aserción (inventada)\n" for m in ns["MUT_LOCAL"]) \
    + "   mutación control_que_se_cae   caída (RuntimeError)\nmutaciones: TODAS COMO SE ESPERA\n"
(d / "forjado.txt").write_text(forjado, encoding="utf-8")
(d / "roja.txt").write_text("ROJA: el módulo no existe\n", encoding="utf-8")
print("ausente :", f(str(d / "no_existe.txt"))[0])
print("roja    :", f(str(d / "roja.txt"))[0])
print("forjado :", f(str(d / "forjado.txt"))[0], "(archivo escrito a mano, sin ninguna corrida)")
import shutil; shutil.rmtree(d)
