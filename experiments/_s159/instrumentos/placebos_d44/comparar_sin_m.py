# -*- coding: utf-8 -*-
"""Control del atajo de evaluar_sin_m.py: la misma semilla del placebo (c) con el evaluador entero y sin M; el detalle
de P2 (veredicto calibrado, sin calibrar, neto, discordantes, noches, falsos, intervalo) tiene que ser idéntico en las
dos reglas y los dos sensores, y la tabla tiene que ver las mismas apagadas y encendidas.
Uso: python comparar_sin_m.py <tmp> <ventana> <salida.txt>"""
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
tmp, ventana, salida = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
filas = {}
for modo in ("entero", "sin_m"):
    jl = tmp / ("cmp_%s_%s.jsonl" % (ventana, modo))
    if jl.exists():
        jl.unlink()
    cmd = [sys.executable, str(AQUI / "placebo_d44.py"), str(tmp / ("cmp_%s_%s" % (ventana, modo))), ventana, "c", "0.5",
           "1", str(jl)] + (["--entero"] if modo == "entero" else [])
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    filas[modo] = [json.loads(l) for l in open(jl, encoding="utf-8")][-1]
claves = sorted(k for k in filas["entero"] if k.startswith("P2|")) + ["apagadas_en_tabla", "encendidas_en_tabla",
                                                                    "otras_diferencias_en_tabla", "apagadas_pedidas",
                                                                    "encendidas_pedidas"]
lineas = []
iguales = True
for k in claves:
    a, b = filas["entero"].get(k), filas["sin_m"].get(k)
    iguales &= a == b
    lineas.append("%-28s %s | entero %s | sin M %s" % (k, "IGUAL" if a == b else "DISTINTO", json.dumps(a), json.dumps(b)))
lineas.append("estado entero: %s" % filas["entero"].get("estado"))
lineas.append("estado sin M:  %s" % filas["sin_m"].get("estado"))
lineas.append("RESULTADO: %s" % ("P2 IDÉNTICO con y sin M" if iguales else "P2 DISTINTO: el atajo no vale"))
salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("\n".join(lineas))
