# -*- coding: utf-8 -*-
"""S150. Sustrato de la prueba de Nevados de Chillan, contado sobre la referencia congelada.
Por sensor y por fase (reposo 2026-09-14 a 09-27; actividad 2026-09-28 a 10-07): pasadas UNICAS de
MIROVA con alerta (tabla u OCR) y pasadas listadas sin alerta (RUTINA, VRP 0), y cuantas alertas
de 1 MW o mas. Pasada unica = (sensor, Fecha_Satelite_UTC); una fila de tabla y otra de OCR de la
misma pasada cuentan una vez (error de S149: el sustrato contado doble).
En el CSV, 'VIIRS' es VIIRS 750 y 'VIIRS375' es VIIRS 375.
Uso: python sustrato_ndc.py [carpeta_congelada]"""
import csv, io, sys, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "_congelado_ndc"
pas = {}
for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    for r in csv.DictReader(open(C / f, encoding="utf-8")):
        if "chill" not in r["Volcan"].lower(): continue
        t = r["Fecha_Satelite_UTC"][:16]
        if not ("2026-09-14" <= t[:10] <= "2026-10-07"): continue
        k = (r["Sensor"], t); alerta = r["Tipo_Registro"].startswith("ALERTA")
        mw = float(r["VRP_MW"] or 0)
        prev = pas.get(k, (False, 0.0, set()))
        pas[k] = (prev[0] or alerta, max(prev[1], mw if alerta else 0.0), prev[2] | {f.split("_")[2][:4]})
c = collections.Counter()
for (s, t), (al, mw, fuentes) in pas.items():
    fase = "reposo" if t[:10] <= "2026-09-27" else "actividad"
    c[(s, fase, "alerta" if al else "sin_alerta")] += 1
    if al and mw >= 1.0: c[(s, fase, "alerta_1MW")] += 1
    if al and fuentes == {"ocr."}: c[(s, fase, "alerta_solo_ocr")] += 1
for s in ("MODIS", "VIIRS375", "VIIRS"):
    for fase in ("reposo", "actividad"):
        print("%-8s %-9s alertas %3d (1 MW o mas %3d, solo OCR %2d) | listadas sin alerta %3d" % (
            s, fase, c[(s, fase, "alerta")], c[(s, fase, "alerta_1MW")], c[(s, fase, "alerta_solo_ocr")], c[(s, fase, "sin_alerta")]))
