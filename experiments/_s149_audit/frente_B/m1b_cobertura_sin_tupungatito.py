# -*- coding: utf-8 -*-
"""Frente B. M1b: el "86 % enero / 95 % febrero" de cobertura de la tabla, es de todos los volcanes
o es solo la ausencia de Tupungatito contada en el denominador?
Instrumento: (1) si un volcan no tuviera filas un mes, lo veria: si, se lista por volcan.
(2) denominador = dias CALENDARIO entre la primera fila del archivo y el fin del mes (no dias con dato),
asi un dia sin ninguna fila cuenta como hueco. Control: Tupungatito en enero debe dar 0 %.
Tambien: las 3 ALERTA_OCR MODIS sin ALERTA de la tabla en la misma llave.
"""
import csv, io, sys, collections
from datetime import datetime, timedelta, date
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
SNAP = ROOT / "data/mirova_reference/mirova_v1_snapshot"
cons = list(csv.DictReader(open(SNAP / "registro_vrp_consolidado.csv", encoding="utf-8")))
ocr = list(csv.DictReader(open(SNAP / "registro_vrp_ocr.csv", encoding="utf-8")))


def es_noche(f):
    return f[11:16] < "10:42" or f[11:16] >= "22:42"


def nk(f):
    return (datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S") - timedelta(hours=16)).date()


vols = sorted(set(r["Volcan"] for r in cons))
ini = date(2026, 1, 10)
fin = nk(max(r["Fecha_Satelite_UTC"] for r in cons))
tiene = collections.defaultdict(set)  # (vol, sensor) -> noches
for r in cons:
    if es_noche(r["Fecha_Satelite_UTC"]):
        tiene[(r["Volcan"], r["Sensor"])].add(nk(r["Fecha_Satelite_UTC"]))
dias = [ini + timedelta(days=i) for i in range((fin - ini).days)]
for m in ("2026-01", "2026-02", "2026-03"):
    dm = [d for d in dias if d.strftime("%Y-%m") == m]
    print("\n%s (%d noches calendario desde %s)" % (m, len(dm), dm[0]))
    for s in ("MODIS", "VIIRS", "VIIRS375"):
        por_vol = {v: sum(1 for d in dm if d in tiene[(v, s)]) for v in vols}
        tot11 = 100.0 * sum(por_vol.values()) / (len(dm) * 11)
        tot10 = 100.0 * sum(n for v, n in por_vol.items() if v != "Tupungatito") / (len(dm) * 10)
        peor = sorted(((n, v) for v, n in por_vol.items() if v != "Tupungatito"))[:2]
        print("  %-8s con Tupungatito en el denominador %.1f %% | sin Tupungatito %.1f %% | Tupungatito %d de %d | los 2 peores del resto: %s" % (
            s, tot11, tot10, por_vol["Tupungatito"], len(dm), peor))
# noches sin NINGUNA fila de ningun sensor (hueco del scraper), enero a marzo
sin = [d for d in dias if d < date(2026, 4, 1) and not any(d in tiene[(v, s)] for v in vols for s in ("MODIS", "VIIRS", "VIIRS375"))]
print("\nNoches calendario sin ninguna fila nocturna de ningun volcan (ene-mar):", sin)
# por noche, cuantos volcanes (de 10) sin fila MODIS en enero
print("Enero, noches con < 8 de 10 volcanes con fila MODIS:", [(str(d), sum(1 for v in vols if v != "Tupungatito" and d in tiene[(v, "MODIS")])) for d in dias if d.strftime("%Y-%m") == "2026-01" and sum(1 for v in vols if v != "Tupungatito" and d in tiene[(v, "MODIS")]) < 8])

print("\n--- ALERTA_OCR de MODIS sin ALERTA de la tabla en la misma llave al minuto")
kc = {}
for r in cons:
    kc.setdefault((r["Volcan"], r["Sensor"], r["Fecha_Satelite_UTC"][:16]), r)
for r in ocr:
    if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA_OCR":
        k = (r["Volcan"], r["Sensor"], r["Fecha_Satelite_UTC"][:16])
        c = kc.get(k)
        if c is None or c["Tipo_Registro"] != "ALERTA_TERMICA":
            print("  ", r["Fecha_Satelite_UTC"], r["Volcan"], "VRP_OCR", r["VRP_MW"], "conf", r["Confianza_Validacion"], "| noche:", es_noche(r["Fecha_Satelite_UTC"]),
                  "| en tabla:", (c["Tipo_Registro"], c["VRP_MW"], c["Distancia_km"]) if c else "SIN FILA")
