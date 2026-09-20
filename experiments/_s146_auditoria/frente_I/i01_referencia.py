# -*- coding: utf-8 -*-
"""I-01. Que hay en la referencia: tipos, fuentes, sensores, dia/noche, duplicados, solapes CONS/OCR.

P1: si la referencia tuviera duplicados, horas locales o filas OCR pisadas por CONS, los conteos
    de abajo lo muestran (duplicados>0, histograma horario corrido, solapes con tipo distinto).
P2: si el loader devolviera vacio, los totales son 0 y se ve.
"""
import sys, io, csv, collections, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import banco_paridad as bp
from datetime import datetime, timezone
DL = ROOT / "experiments/_s145_paridad/_dl_referencia"
VENT = ("2026-09-01", "2026-09-20")
C = collections.Counter

# --- crudo, sin loader
for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    rows = list(csv.DictReader(open(DL / nombre, encoding="utf-8")))
    w = [r for r in rows if VENT[0] <= r["Fecha_Satelite_UTC"][:10] <= VENT[1]]
    print(f"\n== CRUDO {nombre}: {len(rows)} filas, {len(w)} en ventana; rango fechas {min(r['Fecha_Satelite_UTC'] for r in rows)} a {max(r['Fecha_Satelite_UTC'] for r in rows)}")
    print(" sensor x tipo (ventana):", dict(sorted(C((r["Sensor"], r["Tipo_Registro"]) for r in w).items())))
    k = C((r["timestamp"], r["Volcan"], r["Sensor"]) for r in rows)
    print(" claves (timestamp,Volcan,Sensor) repetidas en todo el archivo:", sum(1 for v in k.values() if v > 1))
    # coherencia timestamp epoch vs Fecha_Satelite_UTC
    malos = 0
    for r in w:
        dt = datetime.strptime(r["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if int(float(r["timestamp"])) != int(dt.timestamp()): malos += 1
    print(" filas en ventana con epoch != Fecha_Satelite_UTC leida como UTC:", malos)
    print(" segundos de la hora (ventana):", dict(C(r["Fecha_Satelite_UTC"][17:19] for r in w).most_common(5)))
    print(" minutos mod 5 == 0:", sum(1 for r in w if int(r["Fecha_Satelite_UTC"][14:16]) % 5 == 0), "de", len(w))
    print(" Editado:", dict(C(r["Editado"] for r in w)))
    if "ocr" in nombre:
        print(" confianza x tipo:", dict(C((r["Tipo_Registro"], r["Confianza_Validacion"], r["Requiere_Verificacion"]) for r in w)))
    else:
        print(" RUTINA con VRP != 0:", sum(1 for r in w if r["Tipo_Registro"] == "RUTINA" and float(r["VRP_MW"]) != 0))
        print(" clasif x tipo:", dict(C((r["Tipo_Registro"], r["Clasificacion Mirova"]) for r in w)))
        # retraso entre pasada y primera captura
        lag = []
        for r in w:
            try:
                a = datetime.strptime(r["Fecha_Captura_Chile"], "%Y-%m-%d %H:%M:%S"); p = datetime.strptime(r["Fecha_Proceso_GitHub"], "%Y-%m-%d %H:%M:%S")
                lag.append((p - a).total_seconds() / 3600)
            except Exception: pass
        lag.sort(); n = len(lag)
        print(f" latencia pasada->primera captura (h, hora Chile ambas): p05 {lag[n//20]:.1f} p50 {lag[n//2]:.1f} p95 {lag[n*19//20]:.1f} max {lag[-1]:.1f} n {n}")

# --- via loader del banco
coords = bp._coords_por_volcan()
filas = bp.cargar_referencia_unificada(DL / "registro_vrp_consolidado.csv", DL / "registro_vrp_ocr.csv")
w = [f for f in filas if VENT[0] <= f["fecha_utc"][:10] <= VENT[1]]
print("\n== LOADER: filas en ventana", len(w), "| origen:", dict(C(f["origen"] for f in w)))
dn = C()
for f in w:
    dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    lat, lon = coords[f["volcano"]]
    f["diurna"] = bp.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt)
    dn[(f["sensor_bucket"], f["source"], f["tipo"], "DIA" if f["diurna"] else "NOCHE")] += 1
for k in sorted(dn): print("  ", k, dn[k])
print(" hora UTC de filas NOCTURNAS:", dict(sorted(C(f["fecha_utc"][11:13] for f in w if not f["diurna"]).items())))
print(" hora UTC de filas DIURNAS  :", dict(sorted(C(f["fecha_utc"][11:13] for f in w if f["diurna"]).items())))
# solape CONS / OCR en la misma clave-minuto
porclave = collections.defaultdict(dict)
for f in w: porclave[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])][f["source"]] = f
amb = [v for v in porclave.values() if len(v) == 2]
print(" claves con fila CONS y OCR a la vez:", len(amb), "->", dict(C((v["CONS"]["tipo"], v["OCR"]["tipo"]) for v in amb)))
# OCR a menos de 10 min de una CONS del mismo volcan/sensor (sin ser la misma clave)
print(" filas OCR totales en ventana:", sum(1 for f in w if f["source"] == "OCR"))
json.dump([{k: v for k, v in f.items()} for f in w], open(Path(__file__).parent / "_cache_ref.json", "w", encoding="utf-8"), ensure_ascii=False)
