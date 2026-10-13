# -*- coding: utf-8 -*-
"""F2 M11. Las pasadas V375 'sin_info' (fuera de todo denominador del evaluador) son el 48 % de las pasadas. ¿Que
son y cuanto publica F en ellas? Desglose con los campos de la tabla: rutina_pasada (MIROVA lista ESTA pasada con
VRP 0), noche_con_alerta_sensor. 'sin fila' se infiere como ni rutina_pasada ni otra etiqueta (aprox., declarado).
Pregunta 1: si todo sin_info fuera noche con alerta (senal real cercana), F publicaria parejo en todas; el
desglose separa la parte sin alerta. Ventana abril-agosto 2026."""
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
a = collections.Counter(); por_mes = collections.Counter()
for ruta in sys.argv[1:]:
    for k, v in json.load(open(ruta, encoding="utf-8"))["pasadas"].items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]
        if c["lab"] != "sin_info": continue
        g = ("RUTINA VRP0" if c.get("rutina_pasada") else "sin RUTINA a +-2min") + (" | noche CON alerta" if c.get("noche_con_alerta_sensor") else " | noche SIN alerta")
        a[(g, "n")] += 1; a[(g, "B")] += c["pub"]; a[(g, "F")] += f["pub"]
        if not c.get("rutina_pasada") and not c.get("noche_con_alerta_sensor"):
            por_mes[(dt[:7], "n")] += 1; por_mes[(dt[:7], "F")] += f["pub"]
for g in sorted({k[0] for k in a}):
    n, b, f = a[(g, "n")], a[(g, "B")], a[(g, "F")]
    print("%-45s n %5d | B %4d (%5.1f %%) | F %4d (%5.1f %%)" % (g, n, b, 100 * b / n, f, 100 * f / n))
print("sin RUTINA y noche SIN alerta, por mes (n, F publica):", {m: (por_mes[(m, 'n')], por_mes[(m, 'F')]) for m in sorted({k[0] for k in por_mes})})
