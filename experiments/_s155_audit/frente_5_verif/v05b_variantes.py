# -*- coding: utf-8 -*-
"""Variantes del cociente V750/V375 para ver bajo que definicion salen 1,06 y 0,62 (n 34).
Lee pares_remoto.json (pareados con MIROVA). Sin cambios al repo."""
import json, statistics, os
P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pares_remoto.json"), encoding="utf-8"))
by = {}
for f in P:
    by.setdefault(f["t"], {})[f["b"]] = f
pares = [(v["VIIRS750"], v["VIIRS375"]) for v in by.values() if "VIIRS750" in v and "VIIRS375" in v
         and v["VIIRS750"]["pub"] is not None and v["VIIRS375"]["pub"]]
print("pares con ambos sensores pareados a MIROVA:", len(pares))
def tabla(nombre, fn, cortes):
    print(nombre)
    for lo, hi in cortes:
        e = [fn(a, b) for a, b in pares if lo <= a["zen"] < hi and fn(a, b) is not None]
        if e: print("   %2d-%2d n=%2d mediana %.2f" % (lo, hi, len(e), statistics.median(e)))
for cortes in (((0, 30), (30, 45), (45, 60), (60, 90)), ((0, 40), (40, 90)), ((0, 30), (45, 90))):
    tabla("pub750/pub375 cortes %s" % (cortes,), lambda a, b: a["pub"] / b["pub"] if b["pub"] > 0 else None, cortes)
    tabla("pub750/pc375", lambda a, b: a["pub"] / b["pc_vrp"] if b["pc_vrp"] else None, cortes)
    tabla("(pub750/mir750)/(pub375/mir375)", lambda a, b: (a["pub"] / a["mir"]) / (b["pub"] / b["mir"]) if b["pub"] > 0 and a["pub"] > 0 else None, cortes)
    tabla("mir750/mir375 (MIROVA consigo misma)", lambda a, b: a["mir"] / b["mir"], cortes)

print("\n-- doble razon con V750 TOTAL (suma de todo lo alertado <=5 km del crater, s_in) --")
for cortes in (((0, 30), (30, 45), (45, 60), (60, 90)), ((0, 30), (45, 90))):
    tabla("(tot750/mir750)/(pub375/mir375)", lambda a, b: (a["s_in"] / a["mir"]) / (b["pub"] / b["mir"]) if b["pub"] > 0 and a["s_in"] > 0 else None, cortes)
    tabla("tot750/mir750", lambda a, b: a["s_in"] / a["mir"] if a["s_in"] > 0 else None, cortes)
    tabla("pub750/mir750", lambda a, b: a["pub"] / a["mir"] if a["pub"] > 0 else None, cortes)
