# -*- coding: utf-8 -*-
"""S150. P1 y P5 del pre-registro del A/B de D22: de la lista FIJA de alertas que la conectiva max (F) pierde
contra B (experiments/_s150_debiles/filas.json, abril a agosto), cuantas recupera el brazo F2 (max sin D22).

La clasificacion de camino y etiqueta se importa de experiments/_s150_debiles/clases_rechazo.py (no se
re-deriva despues de ver el resultado). Entrada: las tablas por pasada que arma evaluar_ventana.py para cada
mes con control F y brazo F2 (tabla.json en la carpeta --tmp/<mes>/ de cada corrida).

Prueba antes de despachar: con F contra si mismo (tablas de F contra F), recupera 0 y cambia 0.

  python recuperacion_d22.py tabla_abril.json tabla_mayo.json ...
"""
import collections, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
DEB = AQUI.parent / "_s150_debiles"
# clases_rechazo.py imprime su informe al importarse; se cargan SOLO sus definiciones (MALAS, camino, etiqueta)
# desde su codigo fuente, sin copiarlas: la regla es la misma que uso la investigacion.
import ast, types
_src = (DEB / "clases_rechazo.py").read_text(encoding="utf-8")
_nodos = [n for n in ast.parse(_src).body
          if (isinstance(n, ast.FunctionDef) and n.name in ("camino", "etiqueta"))
          or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "MALAS" for t in n.targets))]
cr = types.SimpleNamespace(); _ns = {}
exec(compile(ast.Module(body=_nodos, type_ignores=[]), str(DEB / "clases_rechazo.py"), "exec"), _ns)
cr.camino, cr.etiqueta, cr.MALAS = _ns["camino"], _ns["etiqueta"], _ns["MALAS"]

FILAS = json.load(open(DEB / "filas.json", encoding="utf-8"))
perdidas = [r for r in FILAS if r["perdida"] and r["b"] == "VIIRS375"]
T = {}
for ruta in sys.argv[1:]:
    T.update(json.load(open(ruta, encoding="utf-8"))["pasadas"])

D22 = "B solo 2.o pase, BT < t_bg+3K (compuerta D22 lo bloquea en ambos)"
grupos = collections.defaultdict(lambda: {"n": 0, "en_tabla": 0, "F": 0, "F2": 0, "claves_recuperadas": []})
for r in perdidas:
    et = cr.etiqueta(r)
    if et == "OCR imagen de otra pasada":
        continue
    confiable = et in ("tabla", "solo OCR, desde 06-13")
    g = grupos[(cr.camino(r), "confiable" if confiable else "OCR antes de 06-13")]
    g["n"] += 1
    v = T.get(r["clave"])
    if v is None or len(v) != 2:
        continue
    g["en_tabla"] += 1
    g["F"] += v["control"]["pub"]; g["F2"] += v["brazo"]["pub"]
    if v["brazo"]["pub"] and not v["control"]["pub"]:
        g["claves_recuperadas"].append(r["clave"])

print("Perdidas de VIIRS 375 de la lista fija (sin las 5 filas OCR con la imagen de otra pasada), por camino y etiqueta:")
for (cam, et), g in sorted(grupos.items()):
    print("  %-70s %-20s n %3d | en las tablas %3d | publica F %3d | publica F2 %3d" % (cam, et, g["n"], g["en_tabla"], g["F"], g["F2"]))
p1 = grupos[(D22, "confiable")]
print("\nP1 (camino D22, etiqueta confiable): F2 publica %d de %d (umbral: 7 de 14; en las tablas %d) | %s" % (
    p1["F2"], p1["n"], p1["en_tabla"], "CUMPLE" if p1["F2"] >= 7 else "FALLA"))
print("   recuperadas:", p1["claves_recuperadas"])
p5 = [g for (cam, et), g in grupos.items() if cam == "B por 1.er pase"]
print("P5 (informativa, camino primer pase): F2 publica %d de %d" % (sum(g["F2"] for g in p5), sum(g["n"] for g in p5)))
