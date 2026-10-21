# -*- coding: utf-8 -*-
"""Comprueba sin bajar granulos que los pares de granulos consecutivos son el volcan partido en el borde.

Fenomeno: si el ROI de 25 km cae en el borde entre dos granulos, cada granulo trae solo una parte del anillo
de fondo; la suma de las dos partes deberia dar el anillo entero de una pasada no partida al mismo cenit.
Pregunta 1: si los pares NO fueran el borde (hora mal guardada, granulo duplicado), lo veria? Si: un
granulo duplicado daria suma ~2 (dos anillos enteros) y una hora mal guardada daria cada miembro ~1.
Pregunta 2: control: pasadas no partidas contra su propia referencia deben dar ~1 (mediana).
Variable: diag_n_bg_anillo (pixeles del anillo de fondo). Referencia: mediana de pasadas de un solo granulo
del mismo volcan y plataforma con cenit a +-3 grados. Denominador: todos los records de los 11 Tier A.
"""
import collections, json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
out = collections.defaultdict(list)
for vol in VOLS:
    recs = json.load(open(RAIZ / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    por = collections.defaultdict(list)
    for r in recs:
        por[r["sensor"]].append((datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M"), r))
    for sensor, l in por.items():
        b = "MODIS" if sensor.startswith("MODIS") else ("VIIRS750" if sensor.endswith("_750") else "VIIRS375")
        p = timedelta(minutes=5 if b == "MODIS" else 6)
        l.sort(key=lambda x: x[0])
        ts = {t for t, _ in l}
        solos = [(r.get("sensor_zenith_deg"), r.get("diag_n_bg_anillo")) for t, r in l
                 if t - p not in ts and t + p not in ts and r.get("diag_n_bg_anillo") and r.get("sensor_zenith_deg") is not None]
        def ref(z):
            xs = [n for zz, n in solos if abs(zz - z) <= 3]
            return statistics.median(xs) if len(xs) >= 5 else None
        d = dict(l)
        for t, r in l:
            if t + p in ts:
                r2 = d[t + p]
                n1, n2, z = r.get("diag_n_bg_anillo"), r2.get("diag_n_bg_anillo"), r.get("sensor_zenith_deg")
                if None in (n1, n2, z) or ref(z) is None:
                    out[b + "|par_sin_dato"].append(1); continue
                out[b + "|suma_par"].append((n1 + n2) / ref(z))
                out[b + "|miembro_menor"].append(min(n1, n2) / ref(z))
                out[b + "|miembro_mayor"].append(max(n1, n2) / ref(z))
                if abs((r2.get("sensor_zenith_deg") or 0) - z) > 5:
                    out[b + "|cenit_distinto>5"].append(1)
        for z, n in solos[::7]:   # control: una muestra de pasadas no partidas
            rz = ref(z)
            if rz:
                out[b + "|control_solo"].append(n / rz)
for k in sorted(out):
    v = out[k]
    if all(x == 1 for x in v) and not k.endswith(("par", "menor", "mayor", "solo")):
        print(f"{k}: n {len(v)}"); continue
    q = statistics.quantiles(v, n=10) if len(v) > 10 else v
    print(f"{k}: n {len(v)} mediana {statistics.median(v):.3f} p10 {q[0]:.3f} p90 {q[-1]:.3f}")
