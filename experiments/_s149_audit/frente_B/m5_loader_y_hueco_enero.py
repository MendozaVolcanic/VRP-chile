# -*- coding: utf-8 -*-
"""Frente B. M5: que entrega hoy el loader canonico (pipeline.mirova_csv_loader.load_mirova_alertas)
en los tramos con defecto, y cuanto pesa el hueco de NUESTRA serie (2026-01-10 a 2026-01-28) en los
recall que parten la ventana el 2026-01-01 (scripts/libro_de_cuentas.py, scripts/paper_numbers.py).
Instrumento: (1) si el loader filtrara por confianza o fecha, los conteos por tramo darian 0 antes del
hito: se imprimen. (2) control: el total debe igualar ALERTA cons + ALERTA_OCR sin llave compartida.
"""
import collections, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa
import csv
SNAP = ROOT / "data/mirova_reference/mirova_v1_snapshot"
al = load_mirova_alertas(cons_path=SNAP / "registro_vrp_consolidado.csv", ocr_path=SNAP / "registro_vrp_ocr.csv")
print("alertas del loader:", len(al), collections.Counter(a["source"] for a in al))


def tramo(f):
    d = f[:10]
    return ("1 <03-01" if d < "2026-03-01" else "2 03-01..06-10" if d < "2026-06-11" else "3 06-11..06-12" if d < "2026-06-13" else "4 >=06-13")


print("\nOCR por tramo: n | con dist_km | dist mediana | bucket")
import statistics as st
for t in sorted(set(tramo(a["fecha_utc"]) for a in al)):
    o = [a for a in al if a["source"] == "OCR" and tramo(a["fecha_utc"]) == t]
    d = [a["dist_km"] for a in o if a["dist_km"] is not None]
    print("  ", t, len(o), len(d), round(st.median(d), 2) if d else None, dict(collections.Counter(a["sensor_bucket"] for a in o)))
# confianza de las filas OCR que el loader deja pasar
conf = {}
for r in csv.DictReader(open(SNAP / "registro_vrp_ocr.csv", encoding="utf-8")):
    conf[(r["timestamp"], r["Volcan"])] = (r["Confianza_Validacion"], r["Editado"])
c = collections.Counter()
for r in csv.DictReader(open(SNAP / "registro_vrp_ocr.csv", encoding="utf-8")):
    if r["Tipo_Registro"] == "ALERTA_TERMICA_OCR":
        c[r["Confianza_Validacion"]] += 1
print("\nALERTA_TERMICA_OCR por Confianza_Validacion (el loader no filtra por confianza):", dict(c))

# share de alertas solo-OCR por bucket y mes (A119 dice 20-39 % de V375 entre marzo y agosto)
print("\nFraccion de alertas del loader que vienen SOLO del OCR, por bucket y mes:")
pm = collections.defaultdict(lambda: [0, 0])
for a in al:
    k = (a["sensor_bucket"], a["fecha_utc"][:7]); pm[k][0] += 1; pm[k][1] += a["source"] == "OCR"
for b in ("MODIS", "VIIRS750", "VIIRS375"):
    print("  ", b, "  ".join("%s %.0f%%(%d)" % (m[5:], 100.0 * pm[(b, m)][1] / pm[(b, m)][0], pm[(b, m)][0]) for m in sorted(set(k[1] for k in pm)) if pm[(b, m)][0]))

# hueco de enero: noches-alerta (volcan, bucket, fecha) 01-10..01-28 fuera de Villarrica, contra el total
print("\nNoches-ALERTA del loader por bucket: total 2026 | en 2026-01-10..01-28 y volcan != Villarrica (nuestra serie no existe ahi)")
for b in ("MODIS", "VIIRS750", "VIIRS375"):
    tot = set((a["volcano"], a["fecha_utc"][:10]) for a in al if a["sensor_bucket"] == b)
    hue = set(k for k in tot if k[1] <= "2026-01-28" and k[0] != "Villarrica")
    print("   %-9s %4d | %3d (%.1f %%)  -> techo de recall por este solo efecto: %.1f %%" % (b, len(tot), len(hue), 100.0 * len(hue) / len(tot), 100.0 * (1 - len(hue) / len(tot))))
