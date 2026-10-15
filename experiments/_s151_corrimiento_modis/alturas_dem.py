# Alturas del terreno (SRTM 90 m, API publica opentopodata.org, sin credenciales) en el crater y en dos
# anillos alrededor (2,5 y 5 km, 8 acimuts). Solo lectura del repo.
#
# POR QUE: el paralaje que queda en una geolocalizacion corregida por terreno en una grilla de 5 km no
# depende de la altura absoluta de la cumbre, sino de cuanto sobresale la cumbre sobre las alturas que
# usa la grilla gruesa alrededor. El anillo es una aproximacion a esas alturas (los puntos de la grilla
# de 5 km caen entre 0 y ~3,5 km del crater).
import json
import math
import time
import urllib.request

import comun

PUNTOS = []
for v, (la, lo) in comun.vents().items():
    PUNTOS.append((v, "vent", 0.0, 0.0, la, lo))
    for r in (2.5, 5.0):
        for k in range(8):
            a = math.radians(45 * k)
            dla = r * math.cos(a) / 111.32
            dlo = r * math.sin(a) / (111.32 * math.cos(math.radians(la)))
            PUNTOS.append((v, "anillo", r, 45 * k, la + dla, lo + dlo))

alturas = []
for i in range(0, len(PUNTOS), 90):
    lote = PUNTOS[i:i + 90]
    locs = "|".join("%.6f,%.6f" % (p[4], p[5]) for p in lote)
    url = "https://api.opentopodata.org/v1/srtm90m?locations=" + locs
    with urllib.request.urlopen(url, timeout=60) as resp:
        res = json.load(resp)
    alturas += [x["elevation"] for x in res["results"]]
    time.sleep(1.2)

out = {}
for p, h in zip(PUNTOS, alturas):
    d = out.setdefault(p[0], {"vent_m": None, "anillo_2_5_m": [], "anillo_5_m": []})
    if p[1] == "vent":
        d["vent_m"] = h
    elif p[2] == 2.5:
        d["anillo_2_5_m"].append(h)
    else:
        d["anillo_5_m"].append(h)
for v, d in out.items():
    ring = [x for x in d["anillo_2_5_m"] + d["anillo_5_m"] if x is not None]
    d["anillo_medio_m"] = round(sum(ring) / len(ring), 1)
    d["relieve_m"] = round(d["vent_m"] - d["anillo_medio_m"], 1)
comun.SALIDAS.mkdir(exist_ok=True)
json.dump({"fuente": "SRTM 90 m via api.opentopodata.org/v1/srtm90m", "volcanes": out},
          open(comun.SALIDAS / "alturas_dem.json", "w", encoding="utf-8"), indent=1)
for v, d in out.items():
    print("%-20s crater %5s m  anillo medio %6.0f m  relieve %6.0f m" % (v, d["vent_m"], d["anillo_medio_m"], d["relieve_m"]))
