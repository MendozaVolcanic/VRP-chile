# -*- coding: utf-8 -*-
"""Verificador: pasadas de HOY (origin/main) donde el OCR dice ALERTA y la tabla, con la misma clave
(volcan, sensor, minuto), dice FALSO_POSITIVO o RUTINA. Es la clase de contradiccion que las reescrituras de
H1 corrigieron a mano. Control positivo: la misma cuenta sobre la copia OCR del 2026-05-29 (afb14c0a9) contra la
tabla de esa fecha debe incluir las 34 de la tanda 1 (si da < 34, el instrumento esta roto)."""
import csv, io, subprocess, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = r"C:\vrp-trabajo\s159-pruebas"; sys.path.insert(0, R)
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
O = "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
def load(ref, p):
    t = subprocess.run(["git", "-C", R, "show", f"{ref}:{p}"], capture_output=True, text=True, encoding="utf-8").stdout
    d = {}
    for r in csv.DictReader(io.StringIO(t)):
        v = normalize_volcano_name(r.get("Volcan"))
        if v: d[(v, normalize_sensor(r.get("Sensor")), r["Fecha_Satelite_UTC"].strip()[:16])] = r
    return d
for ref in ("afb14c0a9", "origin/main"):
    o, c = load(ref, O), load(ref, "latest_consolidado.csv")
    x = [(k, float(o[k]["VRP_MW"] or 0), c[k]["Tipo_Registro"], c[k]["Distancia_km"]) for k in o
         if o[k]["Tipo_Registro"].startswith("ALERTA") and k in c and not c[k]["Tipo_Registro"].startswith("ALERTA")]
    print(ref, "OCR alerta vs tabla no-alerta:", len(x), "de ellas >=1 MW:", sum(v >= 1 for _, v, _, _ in x),
          collections.Counter(t for _, _, t, _ in x))
    for row in sorted(x)[:12]: print("   ", row)
