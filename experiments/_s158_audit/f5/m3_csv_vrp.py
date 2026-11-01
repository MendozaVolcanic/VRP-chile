# -*- coding: utf-8 -*-
"""F5 medicion 3. ¿Que valores de VRP trae la referencia congelada de V1 (Mirova-v1@35a5ea86) por tipo de fila?
Pregunta: el codigo de MIROVA no recorta dL (MIROVA_VIIRS750_VRP.m:83-91), asi que una pasada con alertas puede dar
VRP <= 0, y una sin alertas da NaN (l. 45-52). ¿Como llegan esos casos a la tabla? Si hay VRP negativos o NaN en
RUTINA, el 'negativo limpio' mezcla 'no detecto' con 'detecto y el fondo se comio la senal'.
Instrumento: cuenta crudos del CSV, sin pareo; control positivo: las ALERTA tienen que tener VRP > 0 (el scraper
las define asi, scraper.py:144 segun docs/audit_s139/EJE_1_semantica_etiquetas_referencia.md:41)."""
import csv, collections, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[3] / "experiments" / "_s157_prereg_d25" / "_congelado_v1"
for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    c = collections.Counter(); crudos = collections.Counter(); minimos = {}
    with open(R / nombre, encoding="utf-8", errors="replace") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames
        for r in rd:
            t = (r.get("Tipo_Registro") or "").strip()
            s = (r.get("VRP_MW") or "").strip()
            try:
                v = float(s)
                cat = "neg" if v < 0 else "cero" if v == 0 else "(0,0.01)" if v < 0.01 else "[0.01,0.05]" if v <= 0.05 else ">0.05"
                minimos[t] = min(minimos.get(t, 9e9), v)
            except ValueError:
                cat = "no_numero:" + s[:8]
            c[(t, cat)] += 1
            if cat == "cero" or cat.startswith("no_"):
                crudos[(t, s)] += 1
    print("==", nombre, "| columnas:", cols)
    for k, n in sorted(c.items()):
        print("   %-28s %-14s %6d" % (k[0], k[1], n))
    print("   texto crudo de los VRP cero o no numericos:", dict(crudos))
    print("   minimo VRP por tipo:", minimos)
