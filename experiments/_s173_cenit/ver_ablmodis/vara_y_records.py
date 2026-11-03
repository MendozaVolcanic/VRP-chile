# -*- coding: utf-8 -*-
"""Verificador S173 (ver_ablmodis): la vara y el cenit por un camino propio.
(a) Los 27 records guardados en data/mirova_equivalent/NevadosDeChillan.json del commit f4ec1061d: cenit
    (sensor_zenith_deg), regimen.codigo_sha, via_codigo_mirova, t_max_k, t_bg_k, y las CLAVES del record por sha
    (para ver si registros_iguales puede caer por claves nuevas y no solo por codigo_sha).
(b) Pareo propio de las 27 pasadas con el scraper (consolidado y OCR del snapshot del mismo commit), MODIS,
    +-120 s, y lectura del VRP y del canal; aviso A119 de calidad_referencia_mirova.
Pregunta 1: si el cenit del JSON no fuera el del record, o si el VRP de MIROVA del JSON no fuera el del scraper,
esta comparacion lo ve (compara numero a numero). Pregunta 2: un pareo vacio sale como SIN FILA, no como 0.
Denominador: 27 pasadas (lista del arnes), 2026-09-29 a 2026-11-02.
"""
import csv
import io
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = "C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/repo_f4ec1061d"
sys.path.insert(0, R + "/scripts")
J = "D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/s173-cenit-modis/s173_cenit_modis.json"
P = json.load(open(J, encoding="utf-8"))["pasadas"]
recs = json.load(open("C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/codigo_origin_main/NevadosDeChillan_f4ec1061d.json", encoding="utf-8"))["records"]
idx = {(r.get("datetime_utc"), r.get("sensor")): r for r in recs}
print("records guardados Chillan en f4ec1061d:", len(recs))
print("\n== (a) record guardado por pasada: z_record(JSON) vs sensor_zenith_deg(record), sha, via, t_max_k, t_bg_k, vrp, pc.vrp, n_pix")
claves_por_sha = defaultdict(set)
for e in P:
    r = idx.get((e["dt"], e["sensor"]))
    if r is None:
        print("  SIN RECORD", e["dt"], e["sensor"]); continue
    sha = (r.get("regimen") or {}).get("codigo_sha")
    claves_por_sha[sha] |= set(r.keys())
    pc = r.get("primary_cluster") or {}
    ok_z = e["z_record"] == r.get("sensor_zenith_deg")
    print(f"  {e['dt']} z_json {e['z_record']} z_rec {r.get('sensor_zenith_deg')} {'OK' if ok_z else 'DIF'} sha {str(sha)[:8]} via {r.get('via_codigo_mirova')} t_max {r.get('t_max_k')} t_bg {r.get('t_bg_k')} vrp {r.get('vrp_mw')} pc {pc.get('vrp_mw')} npix {r.get('n_anomalous_pixels')} ver {r.get('product_version')} regimen_keys {sorted((r.get('regimen') or {}).keys())}")
todas = set().union(*claves_por_sha.values())
print("\n== claves del record por codigo_sha (las que FALTAN respecto a la union):")
for sha, ks in claves_por_sha.items():
    print("  ", str(sha)[:8], "faltan:", sorted(todas - ks))
print("== claves del record mas nuevo (79f41069):", sorted(claves_por_sha.get("79f41069727af508397229dca26bbd33418b9e85", set())))

# (b) scraper
try:
    import calidad_referencia_mirova as cal
    print("\n== A119 aviso para la ventana 2026-09-29 a 2026-11-02:")
    cal.avisar("2026-09-29", "2026-11-02")
except Exception as ex:
    print("A119 avisar no corrio:", repr(ex))


def leer(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd), rd.fieldnames


cons, fc = leer(R + "/data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
ocr, fo = leer(R + "/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
print("\n== columnas consolidado:", fc)
print("== columnas ocr:", fo)
print("volcanes (consolidado) con 'hillan':", Counter(r.get("Volcan") for r in cons if "hillan" in (r.get("Volcan") or "")))
print("fechas max consolidado:", max((r.get("Fecha_Satelite_UTC") or "") for r in cons))


def fecha(s):
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(s.strip(), f)
        except Exception:
            pass
    return None


def filas(tabla, dt, tol=120):
    t0 = fecha(dt)
    out = []
    for r in tabla:
        if "hillan" not in (r.get("Volcan") or ""):
            continue
        if (r.get("Sensor") or r.get("Satelite") or "").upper().strip() not in ("MODIS",):
            continue
        t = fecha(r.get("Fecha_Satelite_UTC") or "")
        if t is None:
            continue
        if abs((t - t0).total_seconds()) <= tol:
            out.append(r)
    return out


print("\n== (b) pareo propio +-120 s, MODIS, Chillan: por pasada filas del consolidado y del OCR (VRP, clasificacion, distancia)")
for e in P:
    fcs = filas(cons, e["dt"])
    fos = filas(ocr, e["dt"])
    def res(rs):
        return [(r.get("Fecha_Satelite_UTC"), r.get("VRP_MW"), r.get("Clasificacion") or r.get("Clase"), r.get("Distancia_km"), r.get("Estado") or r.get("Tipo_Registro") or "") for r in rs]
    print(f"  {e['dt']} JSON {e['vrp_mirova_mw']} | CONS {res(fcs)} | OCR {res(fos)}")
