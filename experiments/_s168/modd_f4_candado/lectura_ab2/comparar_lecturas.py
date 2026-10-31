# -*- coding: utf-8 -*-
"""S170: la relectura (tag s170-modd-f4-lectura, con --tag-runner) contra la primera lectura (0240e0040). Tienen que
coincidir en todo salvo el control de procedencia, el veredicto que de él depende y los insumos de la lectura.
Uso: python comparar_lecturas.py <resultado_1.json> <resultado_2.json>"""
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
a, b = (json.load(open(x, encoding="utf-8")) for x in sys.argv[1:3])
QUITAR = ("insumos_lectura", "veredicto")


def limpio(r):
    r = {k: v for k, v in r.items() if k not in QUITAR}
    r["controles"] = {k: v for k, v in r["controles"].items() if k not in ("procedencia", "manifiesto")}
    return r


def dif(x, y, ruta=""):
    if type(x) is not type(y):
        return [ruta]
    if isinstance(x, dict):
        return [d for k in sorted(set(x) | set(y)) for d in (dif(x.get(k), y.get(k), ruta + "/" + str(k)))]
    if isinstance(x, list):
        return [ruta] if len(x) != len(y) else [d for i, (u, v) in enumerate(zip(x, y)) for d in dif(u, v, "%s[%d]" % (ruta, i))]
    return [] if x == y else [ruta]


d = dif(limpio(a), limpio(b))
print("veredicto 1:", a["veredicto"], "| veredicto 2:", b["veredicto"])
print("procedencia 1:", a["controles"]["procedencia"]["estado"], "| 2:", b["controles"]["procedencia"]["estado"],
      "acepta_runner", b["controles"]["procedencia"].get("acepta_runner"))
print("manifiesto 1:", a["controles"]["manifiesto"]["estado"], "| 2:", b["controles"]["manifiesto"]["estado"])
print("diferencias fuera de procedencia, manifiesto, veredicto e insumos: %d %s" % (len(d), d[:20]))
