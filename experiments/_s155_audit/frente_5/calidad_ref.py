# -*- coding: utf-8 -*-
"""S155 frente 5: hitos de calidad de la referencia (A119) que pisa la ventana, y cuantos pares usan filas del
estrato ALERTA_SIN_GEOMETRIA_OCR (VRP propio, sin distancia). Recalcula las medianas por cenit sin ellas."""
import io, json, os, sys, csv, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__)); WT = os.path.abspath(os.path.join(D, "..", "..", ".."))
sys.path.insert(0, os.path.join(WT, "scripts"))
import calidad_referencia_mirova as Q  # noqa
for a in Q.avisos_de_ventana("2026-09-28", "2026-10-19"):
    print("AVISO", a)
tipos = {}
for x in csv.DictReader(open("D:/vrp-trabajo/temporales/frente_5/registro_vrp_ocr_remoto_20261019.csv", encoding="utf-8", errors="replace")):
    if "hill" in x["Volcan"].lower():
        b = "MODIS" if "MODIS" in x["Sensor"] else ("VIIRS750" if x["Sensor"] == "VIIRS" else "VIIRS375")
        tipos[(x["Fecha_Satelite_UTC"][:16], b)] = x["Tipo_Registro"]
ok = json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))
sg = [f for f in ok if f["fuente"] == "ocr" and tipos.get((f["t"], f["b"]), "").startswith("ALERTA_SIN_GEOMETRIA")]
print("pares protegidos con cumulo: %d; de fuente OCR: %d; de ellos ALERTA_SIN_GEOMETRIA_OCR: %d -> %s" % (
    len(ok), sum(1 for f in ok if f["fuente"] == "ocr"), len(sg), ", ".join(f["t"] + " " + f["b"] for f in sg)))
resto = [f for f in ok if f not in sg]
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    out = []
    for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
        T = [f["Rinner"] for f in resto if f["b"] == b and lo <= f["zen"] < hi]
        out.append("%d-%d %.2f (n=%d)" % (lo, hi, st.median(T), len(T)) if T else "%d-%d -" % (lo, hi))
    print("sin SIN_GEOMETRIA, Rinner %s: %s" % (b, " | ".join(out)))
