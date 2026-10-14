# -*- coding: utf-8 -*-
"""F2 M11b. La celda 'sin RUTINA a +-2 min y noche SIN alerta' (pasadas V375 sin veredicto de MIROVA), por satelite
y zona de cenit; n y cuantas publica F. Uso: python m11b_sin_veredicto_por_satelite.py <tablas abril..agosto>"""
import json, sys, collections
a = collections.Counter()
for ruta in sys.argv[1:]:
    for k, v in json.load(open(ruta, encoding="utf-8"))["pasadas"].items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]
        if c["lab"] != "sin_info" or c.get("rutina_pasada") or c.get("noche_con_alerta_sensor"): continue
        p = c.get("plataforma") or "?"; p = "SNPP" if "SNPP" in p else "N20" if "NOAA20" in p else "N21" if "NOAA21" in p else p
        z = c.get("z"); zz = "?" if z is None else "nadir<36" if z < 36 else "medio" if z < 52 else "borde>52"
        for key in (p, zz): a[(key, "n")] += 1; a[(key, "F")] += f["pub"]
print("M11b sin RUTINA y noche SIN alerta (n, F publica, %):", {k: (a[(k, 'n')], a[(k, 'F')], round(100 * a[(k, 'F')] / a[(k, 'n')], 1)) for k in sorted({x[0] for x in a})})
