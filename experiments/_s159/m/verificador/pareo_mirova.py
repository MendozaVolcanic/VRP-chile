# S159 M verificador: pareo de MIROVA (CSV del scraper, canal tabla + OCR) para los 12 cambios de publicacion,
# con ventana de +-10 min (no solo hora exacta), y tasa base de desfase de 5 min en el corpus MODIS.
# Pregunta 1: si el pareo exacto perdiera filas de la misma pasada, lo veria? Si: busco +-10 min y cuento cuantas
# veces en todo el corpus MODIS 2026 la fila de MIROVA cae a +-5 min y no en la hora exacta.
# Pregunta 2: control positivo: Lascar 2026-02-11 07:00 debe dar ALERTA 0,48 a 1,41 km.
import csv, json, sys
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[4]
sys.stdout.reconfigure(encoding="utf-8")
ALIAS = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "NevadosDeChillan": "Nevados de Chillan",
         "PlanchonPeteroa": "PlanchonPeteroa", "Lascar": "Lascar", "Lastarria": "Lastarria", "Chaiten": "Chaiten",
         "Llaima": "Llaima", "Villarrica": "Villarrica", "Copahue": "Copahue", "Isluga": "Isluga",
         "Tupungatito": "Tupungatito"}
filas = []
for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    for r in csv.DictReader(open(RAIZ / "data/mirova_reference/mirova_v1_snapshot" / nombre, encoding="utf-8")):
        if r.get("Sensor") == "MODIS":
            r["_t"] = datetime.strptime(r["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M"); r["_src"] = nombre[:14]
            filas.append(r)
volc_csv = Counter(r["Volcan"] for r in filas)
print("volcanes en CSV MODIS:", dict(volc_csv))
CASOS = [("PuyehueCordonCaulle", "2026-06-19 01:15"), ("PuyehueCordonCaulle", "2026-06-30 07:00"),
         ("Lastarria", "2026-02-24 07:05"), ("NevadosDeChillan", "2026-06-01 08:15"), ("Chaiten", "2026-03-13 06:35"),
         ("Lascar", "2026-02-11 07:00"), ("Lascar", "2026-04-01 07:05"), ("NevadosDeChillan", "2026-01-19 02:40")]
for v, t in CASOS:
    t0 = datetime.strptime(t, "%Y-%m-%d %H:%M")
    h = [(r["Fecha_Satelite_UTC"][:16], r["_src"], r["VRP_MW"], r["Distancia_km"], r["Tipo_Registro"])
         for r in filas if r["Volcan"].replace(" ", "").lower().startswith(ALIAS[v].replace(" ", "").lower()[:8])
         and abs((r["_t"] - t0).total_seconds()) <= 600]
    print(v, t, "->", h)
# tasa base: records MODIS de data/ en 2026-02..2026-10, fila MIROVA exacta vs solo a +-5 min
c = Counter()
for v, alias in ALIAS.items():
    p = RAIZ / "data/mirova_equivalent" / f"{v}.json"
    idx = {}
    for r in filas:
        if r["Volcan"].replace(" ", "").lower().startswith(alias.replace(" ", "").lower()[:8]):
            idx.setdefault(r["_t"], r)
    for rec in json.load(open(p, encoding="utf-8"))["records"]:
        if not rec["sensor"].startswith("MODIS") or not ("2026-02-15" <= rec["datetime_utc"] < "2026-10-18"):
            continue
        t = datetime.strptime(rec["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        if t in idx: c["exacta"] += 1
        elif (t - timedelta(minutes=5)) in idx or (t + timedelta(minutes=5)) in idx: c["solo +-5 min"] += 1
        else: c["ninguna"] += 1
print("tasa base, records MODIS 2026-02-15..2026-10-17 de los 11 Tier A:", dict(c))
