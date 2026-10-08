# -*- coding: utf-8 -*-
"""S150 frente B. (a) Contrasta la marca por record `_mirova_confirmed` del tablero (cruce
+-60 min contra data/mirova/NevadosDeChillan.json, que es SOLO el canal CONS) con la verdad
por pasada (alerta de MIROVA en CONS u OCR a +-10 min de la misma adquisicion). Esa marca es la
que pinta en la tarjeta "MIROVA publico en esta pasada" y la que exime de los filtros de
artefacto. (b) Reconstruye lo que la tarjeta de index (latestDetection, ultima deteccion en
48 h) habria mostrado hora a hora durante las noches de actividad.

Preguntas del instrumento:
1. Si la marca fuera siempre falsa o siempre verdadera, la tabla de contingencia lo veria
   (cuatro celdas). Control: 2026-10-01 05:24 NOAA21 tiene alerta solo en OCR.
2. Si el pareo estuviera muerto, 'alerta en la pasada' daria 0 en todas las filas.
Ventana: 2026-09-20 a 2026-10-02 07:35 UTC.
"""
import json, sys, collections
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
t = json.load(open(AQUI / "tabla_ndc.json", encoding="utf-8"))["filas"]

tab = collections.Counter()
casos = collections.defaultdict(list)
for x in t:
    if not x["ix_card"]:
        continue  # la marca solo se ve en la tarjeta cuando el record es la ultima deteccion
    alerta = any(m["tipo"].startswith("ALERTA") for m in x["mirova"])
    solo_ocr = alerta and all(m["fuente"] == "OCR" for m in x["mirova"] if m["tipo"].startswith("ALERTA"))
    k = ("marca_T" if x["ix_conf"] else "marca_F", "alerta_en_pasada" if alerta else "sin_alerta_en_pasada")
    tab[k] += 1
    if x["ix_conf"] != alerta:
        casos[k].append(f"{x['dt']} {x['sensor']} {x['ix_chart']:.2f} MW"
                        + (" (alerta solo OCR)" if solo_ocr else "")
                        + (" MIROVA en la pasada: " + ",".join(m['tipo'] for m in x['mirova']) if x['mirova'] else " MIROVA: sin fila"))
print("contingencia (records elegibles para la tarjeta):")
for k, v in sorted(tab.items()):
    print(" ", k, v)
for k, v in casos.items():
    print("\n", k, "->", len(v))
    for c in v:
        print("   ", c)

# (b) tarjeta hora a hora
def ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")
elig = [x for x in t if x["ix_card"]]
print("\nTarjeta de index (ultima deteccion 48 h), muestreada cada hora en las noches con alertas:")
h = datetime(2026, 9, 28, 4, 0)
prev = None
while h <= datetime(2026, 10, 2, 9, 0):
    vent = [x for x in elig if h - timedelta(hours=48) <= ts(x["dt"]) <= h]
    if vent:
        mx = max(ts(x["dt"]) for x in vent)
        ult = max((x for x in vent if ts(x["dt"]) == mx), key=lambda x: x["ix_chart"])
        s = f"{ult['ix_chart']:.2f} MW {ult['ix_level']} ({ult['dt']} {ult['sensor']}, marca MIROVA={ult['ix_conf']})"
    else:
        s = "sin deteccion"
    max48 = max((x["ix_chart"] for x in vent), default=0)
    linea = f"{s} | max 48 h {max48:.2f}"
    if linea != prev:
        print(f"  desde {h:%m-%d %H:%M}: {linea}")
        prev = linea
    h += timedelta(hours=1)
