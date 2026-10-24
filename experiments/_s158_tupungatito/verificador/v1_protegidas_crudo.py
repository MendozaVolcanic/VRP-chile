# -*- coding: utf-8 -*-
"""Verificador S158. Lista TODAS las filas de Tupungatito VIIRS375 con VRP >= 1 MW en los dos CSV crudos del
scraper (consolidado y OCR), sin pasar por banco_paridad: cualquier tipo, cualquier hora, cualquier distancia.
Sirve para ver qué deja fuera g_protegidas.py (diurnas, SIN_GEOMETRIA, FALSO_POSITIVO, otras ventanas).

Uso: python -I v1_protegidas_crudo.py <dir_con_los_dos_csv>
"""
import csv
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = Path(sys.argv[1])
salida = []
for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    with open(D / nombre, encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    tup = [f for f in filas if f["Volcan"] == "Tupungatito" and f["Sensor"] == "VIIRS375"]
    fechas = sorted(f["Fecha_Satelite_UTC"] for f in tup)
    salida.append(f"== {nombre}: {len(tup)} filas Tupungatito VIIRS375, de {fechas[0]} a {fechas[-1]}")
    tipos = {}
    for f in tup:
        tipos[f["Tipo_Registro"]] = tipos.get(f["Tipo_Registro"], 0) + 1
    salida.append(f"   tipos: {tipos}")
    for f in sorted(tup, key=lambda f: f["Fecha_Satelite_UTC"]):
        try:
            v = float(f["VRP_MW"])
        except ValueError:
            continue
        if v >= 1.0:
            extra = ""
            if "Distancia_aprox_km" in f:
                extra = (f" aprox={f['Distancia_aprox_km']} [{f['Distancia_aprox_min_km']},{f['Distancia_aprox_max_km']}]"
                         f" metodo={f['Distancia_aprox_metodo']} zen={f.get('Zenith_Sat_deg')} azi={f.get('Azimut_Sat_deg')}")
            salida.append(f"   {f['Fecha_Satelite_UTC']}  {f['Tipo_Registro']:26s} VRP {v:6.2f}  dist {f['Distancia_km']:>6s}"
                          f"  clase {f['Clasificacion Mirova']}{extra}")
txt = "\n".join(salida)
print(txt)
(Path(__file__).resolve().parent / "v1_protegidas_crudo_salida.txt").write_text(txt + "\n", encoding="utf-8")
