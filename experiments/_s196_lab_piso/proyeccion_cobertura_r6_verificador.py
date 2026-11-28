# -*- coding: utf-8 -*-
"""i13 (R6FN-102): días de MODIS diurno por volcán desde la frontera y en qué fin la cobertura pasaría el 5 % si cada
día nuevo agrega una noche desigual (lo que pasó del 2026-11-15 al 2026-11-26). Lee i02_pasadas.pkl e i01_resultado_mio.json."""
import collections
import json
import pickle
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
d = pickle.load(open(AQUI / "i02_pasadas.pkl", "rb"))
dias = collections.defaultdict(set)
for p in d["prod"]:
    if p["sensor"].startswith("MODIS") and p["elev"] > 0:
        dias[p["vol"]].add(p["dt"].date().isoformat())
cob = json.loads((AQUI / "i01_resultado_mio.json").read_text(encoding="utf-8"))["cobertura"]
for vol, c in cob.items():
    k = 0
    while (c["desiguales"] + k) / (c["noches"] + k) <= 0.05:
        k += 1
    print("%-17s días con MODIS diurno en prod: %2d (%s a %s) | desiguales %d de %d | pasa el 5 %% con fin %s" % (
        vol, len(dias[vol]), min(dias[vol]), max(dias[vol]), c["desiguales"], c["noches"],
        (date(2026, 11, 26) + timedelta(days=k)).isoformat()))
