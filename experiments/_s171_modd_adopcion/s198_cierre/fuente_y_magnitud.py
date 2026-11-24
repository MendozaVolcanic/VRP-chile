"""S198: fuente en MIROVA (tabla consolidada o sólo OCR) y razón vía/MIROVA de las protegidas que cuentan para el plazo.

Lee protegidas_posteriores_encendido.csv (salida de guardia_cierre.py), la tabla consolidada fresca de Mirova-v1 y los
records MODIS de producción. La magnitud de la vía es la del tablero: primary_cluster.vrp_mw (o vrp_mw sin cúmulo).
Uso (desde la raíz de un checkout de origin/main):
  python experiments/_s171_modd_adopcion/s198_cierre/fuente_y_magnitud.py <protegidas.csv> <consolidado.csv>
"""
import csv
import io
import json
import statistics
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
prot_csv, cons_csv = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(prot_csv, encoding="utf-8")))
nom = {"NevadosDeChillan": "Nevados de Chillan", "Chaiten": "Chaiten"}
cons = {}
for r in csv.DictReader(open(cons_csv, encoding="utf-8")):
    if r.get("Sensor") == "MODIS":
        cons[(r["Volcan"], r["Fecha_Satelite_UTC"][:16])] = r
recs = {}
for v in nom:
    d = json.load(open(f"data/mirova_equivalent/{v}.json", encoding="utf-8"))
    for r in d["records"]:
        if "MODIS" in r.get("sensor", ""):
            recs[(v, str(r["datetime_utc"])[:16].replace("T", " "))] = r
razones, ftab, n = [], 0, 0
for r in rows:
    if r["cuenta_plazo"] != "True":
        continue
    n += 1
    c = cons.get((nom[r["volcano"]], r["fecha_utc"]))
    fuente = "tabla" if c and float(c["VRP_MW"] or 0) >= 1 else "solo OCR/otra"
    ftab += fuente == "tabla"
    rec = recs.get((r["volcano"], r["fecha_utc"]))
    pc = (rec or {}).get("primary_cluster") or {}
    vt = pc.get("vrp_mw", (rec or {}).get("vrp_mw"))
    m = float(r["vrp_mirova_mw"])
    if r["prod_pub"] == "True" and vt:
        razones.append(vt / m)
    print(f"{r['orden']:>3} {r['volcano']:<17} {r['fecha_utc']} MIROVA {m:6.2f} MW [{fuente}] "
          f"via {vt if vt is None else round(vt, 2)} MW K_pub={r['guardia_pub']}")
print(f"\nprotegidas que cuentan: {n}; de la tabla consolidada: {ftab}")
print(f"razon via/MIROVA en las {len(razones)} publicadas: mediana {statistics.median(razones):.3f}, "
      f"min {min(razones):.3f}, max {max(razones):.3f}")
