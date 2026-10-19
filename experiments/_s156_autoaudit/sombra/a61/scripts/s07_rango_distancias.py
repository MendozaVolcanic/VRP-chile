# -*- coding: utf-8 -*-
"""Cuantas alertas VIIRS de PCC (tabla CONS, sin RUTINA) caen entre 7,65 y 8,55 km. Uso: python -I s07_rango_distancias.py <consolidado.csv>"""
import csv, sys
d = [float(r["Distancia_km"]) for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))
     if "Puyehue" in r["Volcan"] and r["Tipo_Registro"] != "RUTINA" and r["Sensor"] in ("VIIRS", "VIIRS375")]
print(f"alertas VIIRS PCC: {len(d)}; entre 7,65 y 8,55 km: {sum(7.649 <= x <= 8.551 for x in d)}")
