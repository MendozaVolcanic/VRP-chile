# -*- coding: utf-8 -*-
"""S150 frente B. Cuenta alertas de MIROVA (CONS, ALERTA_TERMICA) publicadas con el sol sobre el
horizonte, que nuestro store rechaza siempre (store.py:179 _reject_daytime con
ENABLE_DAYTIME_MODIS=False). Usa la MISMA funcion de elevacion solar del store, importada.

Preguntas del instrumento:
1. Si todas las alertas fueran diurnas o ninguna, se veria en el conteo por sensor; control
   positivo: 2026-10-01 18:42 Nevados de Chillan VIIRS375 (15:42 hora local) debe salir diurna.
2. Si la funcion de elevacion devolviera basura, todas las MODIS nocturnas de 01-08 UTC saldrian
   diurnas: se imprime el conteo nocturno al lado.
Ventana: todo el CSV consolidado remoto descargado hoy (2026-01-10 a 2026-10-08).
"""
import csv, sys, collections
from datetime import datetime
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2]))
from pipeline.store import _solar_elevation  # noqa: E402
import yaml  # noqa: E402

vol = yaml.safe_load(open(AQUI.parents[2] / "volcanoes.yaml", encoding="utf-8"))
vol = vol["volcanoes"] if isinstance(vol, dict) else vol
coords = {}
for v in vol:
    coords[v["name"]] = (v["lat"], v["lon"])
alias = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "PlanchonPeteroa": "PlanchonPeteroa", "Peteroa": "PlanchonPeteroa"}
c = collections.Counter()
ndc = []
for r in csv.DictReader(open(AQUI / "datos" / "consolidado.csv", encoding="utf-8")):
    if r["Tipo_Registro"] != "ALERTA_TERMICA":
        continue
    nombre = alias.get(r["Volcan"], r["Volcan"].replace(" ", ""))
    if nombre not in coords:
        c["sin_coord"] += 1
        continue
    dt = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
    el = _solar_elevation(*coords[nombre], dt)
    k = "diurna" if el > 0 else "nocturna"
    c[(r["Sensor"], k)] += 1
    if k == "diurna" and dt >= datetime(2026, 9, 1):
        ndc.append(f"{dt} {nombre} {r['Sensor']} {r['VRP_MW']} MW d={r['Distancia_km']} elev={el:.0f}")
print({str(k): v for k, v in sorted(c.items(), key=str)})
print("alertas diurnas desde 2026-09-01:")
for s in ndc:
    print("  ", s)
