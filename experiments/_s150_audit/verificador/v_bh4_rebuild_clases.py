"""Verificador S150, hallazgo B-H4.

Pregunta: ¿la funcion real rebuild() de scripts/rebuild_mirova_from_consolidado.py
descarta una alerta MIROVA de clase 'Moderado' (>= 10 MW) y la deja fuera del JSON
que lee el dashboard?

Preguntas del instrumento:
1. Si el filtro estuviera roto (dejara pasar todo), ¿lo veria? Si: el control
   negativo (fila NULO) tendria que aparecer en el JSON y la fila Moderado tambien.
2. Si el instrumento estuviera muerto (rebuild no escribe), ¿se veria distinto? Si:
   el control positivo (fila 'Bajo' de 7 MW) tiene que aparecer; si el JSON sale vacio
   el resultado es SIN DATO, no 'descarta'.

No escribe en el repo: REPO del modulo se redirige a un directorio temporal.
"""
import csv
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "rb", REPO / "scripts" / "rebuild_mirova_from_consolidado.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

tmp = Path(tempfile.mkdtemp(prefix="v_bh4_"))
(tmp / "data" / "mirova").mkdir(parents=True)
rb.REPO = tmp  # rebuild() arma dest con el REPO global del modulo

cols = ["Volcan", "Fecha_Satelite_UTC", "Sensor", "VRP_MW", "Distancia_km",
        "Clasificacion Mirova"]
filas = [
    ["Villarrica", "2026-10-01 05:00:00", "VIIRS375", "7.00", "0.5", "Bajo"],          # control positivo
    ["Villarrica", "2026-10-02 05:00:00", "VIIRS375", "35.00", "0.5", "Moderado"],     # caso a probar
    ["Villarrica", "2026-10-03 05:00:00", "MODIS", "250.00", "0.5", "Alto"],           # caso a probar
    ["Villarrica", "2026-10-04 05:00:00", "VIIRS375", "3.00", "0.5", "NULO"],          # control negativo
]
src = tmp / "fake.csv"
with open(src, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(cols)
    w.writerows(filas)

rb.rebuild("Villarrica", "Villarrica", source=src)
out = json.loads((tmp / "data" / "mirova" / "Villarrica.json").read_text(encoding="utf-8"))
print("RESULTADO records en el JSON:")
for r in out["records"]:
    print("  ", r["datetime_utc"], r["sensor"], r["VRP_MW"], r["clasificacion"])
print("control positivo (Bajo 7 MW) presente:", any(r["clasificacion"] == "Bajo" for r in out["records"]))
print("Moderado presente:", any(r["clasificacion"] == "Moderado" for r in out["records"]))
print("Alto presente:", any(r["clasificacion"] == "Alto" for r in out["records"]))
print("NULO presente (debe ser False):", any(r["clasificacion"] == "NULO" for r in out["records"]))
