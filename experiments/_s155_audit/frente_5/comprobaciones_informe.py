# -*- coding: utf-8 -*-
"""S155 frente 5: cifras sueltas que cita el INFORME y que no imprime otro script (rango de BT maxima por sensor en
protegidos, pixel alertado mas lejano, casos con control de membresia)."""
import json, os, re
D = os.path.dirname(os.path.abspath(__file__))
ok = json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    v = [f["btmax"] for f in ok if f["b"] == b]
    print("%s BT max por pasada protegida: min %.2f max %.2f (n=%d)" % (b, min(v), max(v), len(v)))
WT = os.path.abspath(os.path.join(D, "..", "..", ".."))
import sys; sys.path.insert(0, D)
recs = json.load(open(os.path.join(WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]
def bk(s):
    s = s.upper(); return "MODIS" if "MODIS" in s else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
idx = {(r["datetime_utc"][:16], bk(r["sensor"])): r for r in recs}
dmax = max(p["dist_km"] for f in ok for p in idx[(f["t"], f["b"])]["anomaly_pixels"])
print("pixel alertado mas lejano en protegidos: %.2f km" % dmax)
txt = open(os.path.join(D, "seleccion_detalle_salida.txt"), encoding="utf-8").read()
ctl = re.findall(r"control: suma de PUB = ([0-9.]+) \(pc_sum ([0-9.]+)\)", txt)
print("controles de membresia: %d; todos iguales: %s" % (len(ctl), all(a == b for a, b in ctl)))
lej = []
for f in ok:
    r = idx[(f["t"], f["b"])]
    tot = sum(p["vrp_mw"] for p in r["anomaly_pixels"])
    fuera = sum(p["vrp_mw"] for p in r["anomaly_pixels"] if p["dist_km"] > 5.0)
    if fuera > 0 or any(p["dist_km"] > 5.0 for p in r["anomaly_pixels"]):
        lej.append((f["t"], f["b"], round(fuera, 3), round(tot, 3), max(p["dist_km"] for p in r["anomaly_pixels"])))
print("protegidos con algun pixel alertado a mas de 5 km: %d -> %s" % (len(lej), lej))
print("max fraccion de VRP de escena fuera de 5 km: %.3f" % max([a[2] / a[3] for a in lej if a[3] > 0] or [0]))
