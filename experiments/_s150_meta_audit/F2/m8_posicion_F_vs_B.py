# -*- coding: utf-8 -*-
"""F2 M8. ¿Mueve `max` el cumulo publicado? Ningun criterio de posicion entra en la evaluacion por meses de S150
(P1, P2, P4, P5, C8b). En las pasadas V375 que AMBOS brazos publican, separacion entre centroides de cumulo B y F.
Pregunta 1: si `max` moviera cumulos, la cola >2 km lo mostraria. Pregunta 2: control, separacion 0 exacta en
la mayoria (mismo pixel) demuestra que leo posiciones reales y no None."""
import json, sys, io, math, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def hav(a, b, c, d):
    p = math.radians; x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))
cnt = collections.Counter(); ej = []
for ruta in sys.argv[1:]:
    for k, v in json.load(open(ruta, encoding="utf-8"))["pasadas"].items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]
        if not (c["pub"] and f["pub"]): continue
        if None in (c["pc_lat"], f["pc_lat"]): cnt[(c["lab"], "sin posicion")] += 1; continue
        d = hav(c["pc_lat"], c["pc_lon"], f["pc_lat"], f["pc_lon"])
        b = "0" if d < 1e-6 else "<0.4" if d <= .4 else "0.4-2" if d <= 2 else ">2"
        cnt[(c["lab"], b)] += 1
        if d > 2 and c["lab"] == "pos": ej.append((k, round(d, 2), c["pc_dist"], f["pc_dist"]))
for k, n in sorted(cnt.items()): print(k, n)
print("positivas con cumulo F a >2 km del de B:", len(ej)); [print("  ", e) for e in ej[:15]]
