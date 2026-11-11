# -*- coding: utf-8 -*-
"""Inventario de entradas de la bitacora (tasks/LOOP_OBJETIVOS.md seccion 6) de S171 a S178
que tocan el eje MODIS. Fuente: copia de loop/activo en 0472cd95e.

Las dos preguntas del instrumento:
1. Si el inventario estuviera roto (no encuentra entradas), se veria: imprime el total de
   entradas por sesion y el total con palabra clave; un 0 salta a la vista.
2. Si el instrumento estuviera muerto (archivo vacio), el total de entradas seria 0 y lo dice.
Control positivo: la entrada "vía «código MIROVA» de MODIS ENCENDIDA" tiene que salir marcada.
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RUTA = r"D:\vrp-trabajo\temporales\s179-audit\loop\tasks\LOOP_OBJETIVOS.md"
lineas = open(RUTA, encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(lineas) if l.startswith("## 6."))
entradas = []
actual = None
for i in range(ini + 1, len(lineas)):
    l = lineas[i]
    if l.startswith("## ") and not l.startswith("### "):
        break
    if l.startswith("### "):
        actual = {"linea": i + 1, "titulo": l[4:], "cuerpo": []}
        entradas.append(actual)
    elif actual is not None:
        actual["cuerpo"].append(l)
CLAVES = re.compile(r"MODIS|MOD-D|guardia|reversi[oó]n|#93[345]|#938|auto.?audit|audit semanal|"
                    r"retrospectiva|retro\b|fila 4|cambia_sin_pasadas|via_codigo|mirova_v750_codigo|"
                    r"vigilancia_guardia|s173-regla|adopci[oó]n", re.I)
def sesion(t):
    m = re.search(r"S(17\d)", t)
    return m.group(1) if m else "?"
tot = {}
marc = {}
for e in entradas:
    s = sesion(e["titulo"])
    if s not in ("171", "172", "173", "174", "175", "176", "177", "178"):
        continue
    texto = e["titulo"] + "\n" + "\n".join(e["cuerpo"])
    n = len(CLAVES.findall(texto))
    tot[s] = tot.get(s, 0) + 1
    if n:
        marc[s] = marc.get(s, 0) + 1
    print(f"{e['linea']:5d}\tS{s}\tclaves={n:3d}\tcar={len(texto):6d}\t{e['titulo'][:150]}")
print("\nEntradas por sesion (total / con palabra clave del eje):")
for s in sorted(tot):
    print(f"  S{s}: {tot[s]} / {marc.get(s, 0)}")
print("Total:", sum(tot.values()), "/", sum(marc.values()))
ctrl = [e for e in entradas if "ENCENDIDA en producci" in e["titulo"]]
print("Control positivo (entrada del encendido encontrada):", len(ctrl))
