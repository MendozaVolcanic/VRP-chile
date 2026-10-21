# -*- coding: utf-8 -*-
"""Verificador: (a) MIROVA y nosotros contra el cenital por separado; (b) pasadas ALERTA_SIN_GEOMETRIA_OCR
excluidas del universo (sensibilidad del estrato nadir); (c) restriccion a cenit <=40 que pide D17 (S141)."""
import csv, io, json, math, statistics as st, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = Path("D:/vrp-trabajo/worktrees/s157-magnitud-chillan")
d = json.loads((W / "experiments/_s157_magnitud_chillan/a_pasadas_salida.json").read_text(encoding="utf-8"))
P = d["pasadas"]
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    return sum((x - ma) * (z - mb) for x, z in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((z - mb) ** 2 for z in b))
print("== (a) por sensor: corr(log M, cenital), corr(log S_in, cenital), corr(log G, cenital)")
for b in ("VIIRS375", "VIIRS750"):
    g = [p for p in P if p["b"] == b]
    z = [p["cenital"] for p in g]
    print("  %s n%d  M: %.2f  S_in: %.2f  G: %.2f   (solo M>=5: n%d M %.2f S %.2f)" % (
        b, len(g), corr([math.log(p["M"]) for p in g], z), corr([math.log(p["S_in"]) for p in g], z), corr([math.log(p["G"]) for p in g], z),
        len([p for p in g if p["M"] >= 5]),
        corr([math.log(p["M"]) for p in g if p["M"] >= 5], [p["cenital"] for p in g if p["M"] >= 5]),
        corr([math.log(p["S_in"]) for p in g if p["M"] >= 5], [p["cenital"] for p in g if p["M"] >= 5])))
    for zb in ("<30", "30-50", ">=50"):
        gg = [p for p in g if p["banda_cenital"] == zb]
        print("     %-5s M med %.2f  S_in med %.2f" % (zb, st.median(p["M"] for p in gg), st.median(p["S_in"] for p in gg)))
print("== (c) cenit <= 40 contra > 40 (D17, S141)")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    lo = [p for p in P if p["b"] == b and p["cenital"] <= 40]; hi = [p for p in P if p["b"] == b and p["cenital"] > 40]
    print("  %s <=40 n%d R %.2f G %.2f G_area %.2f | >40 n%d R %.2f G %.2f G_area %.2f" % (
        b, len(lo), st.median(p["R"] for p in lo), st.median(p["G"] for p in lo), st.median(p["G_area"] for p in lo),
        len(hi), st.median(p["R"] for p in hi), st.median(p["G"] for p in hi), st.median(p["G_area"] for p in hi)))
print("== (b) ALERTA_SIN_GEOMETRIA_OCR de Chillan en la ventana")
ocr = list(csv.DictReader(open("D:/vrp-trabajo/temporales/s157_magnitud/verificador/ref_run/registro_vrp_ocr.csv", encoding="utf-8")))
recs = json.loads((W / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))["records"]
def bk(s):
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
def bk_ref(s):
    return {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750", "MODIS": "MODIS"}.get(s, s)
for r in ocr:
    if "Chill" not in r["Volcan"] or r["Tipo_Registro"] != "ALERTA_SIN_GEOMETRIA_OCR" or r["Fecha_Satelite_UTC"][:10] < "2026-09-18":
        continue
    t = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
    b = bk_ref(r["Sensor"])
    hit = [x for x in recs if bk(x["sensor"]) == b and abs(datetime.strptime(x["datetime_utc"], "%Y-%m-%d %H:%M") - t) <= timedelta(minutes=2)]
    s = None
    if hit:
        x = hit[0]
        s = sum(p["vrp_mw"] for p in (x.get("anomaly_pixels") or []) if p["dist_km"] is not None and p["dist_km"] <= 5)
    print("  %s %-8s M %6s  nuestro S_in %s  cenital %s  G %s" % (r["Fecha_Satelite_UTC"][:16], b, r["VRP_MW"],
          None if s is None else round(s, 2), hit[0].get("sensor_zenith_deg") if hit else None,
          round(s / float(r["VRP_MW"]), 2) if s is not None and float(r["VRP_MW"] or 0) > 0 else None))
