# -*- coding: utf-8 -*-
"""S155 frente 5: records de Chillan dentro de la ventana reprocesada con K que siguen siendo C0 (sin `regimen`).
Pregunta del instrumento: `regimen` falta en todo record escrito antes de que existiera el campo; si el reproceso con
K los hubiera reescrito, lo traerian. Se imprime lo que el tablero veria (distance_class, pc) y la fila de MIROVA."""
import io, json, os, sys, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
recs = json.load(open(os.path.join(WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]
ref = [x for x in csv.DictReader(open("D:/vrp-trabajo/temporales/frente_5/registro_vrp_consolidado_remoto_20261019.csv",
       encoding="utf-8", errors="replace")) if "hill" in x["Volcan"].lower()]
for r in recs:
    if r["datetime_utc"] >= "2026-09-18" and not r.get("regimen"):
        pc = r.get("primary_cluster") or {}
        m = [(x["Fecha_Satelite_UTC"], x["Sensor"], x["VRP_MW"], x["Tipo_Registro"]) for x in ref
             if x["Fecha_Satelite_UTC"][:13] == r["datetime_utc"][:13] and x["Sensor"] == "MODIS"]
        print(r["datetime_utc"], r["sensor"], r["granule"], "proc", r.get("processed_utc"), "| dclass", r.get("distance_class"),
              "pc", pc.get("vrp_mw"), pc.get("centroid_dist_km"), pc.get("d9_capped"), "| vrp_mw", r.get("vrp_mw"),
              "n_anom", r.get("n_anomalous_pixels"), "t1", r.get("triggered_test1"), "| MIROVA", m)
