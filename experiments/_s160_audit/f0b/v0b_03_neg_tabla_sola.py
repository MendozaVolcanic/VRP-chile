# -*- coding: utf-8 -*-
"""F0b S160: que pasadas son negativo limpio con tabla sola y no con la referencia de S158, y tienen nti_max > -0,87.
Pregunta 1/2: si la etiqueta no dependiera de la referencia, la lista saldria vacia; que salga con nombres concretos
es el control positivo de que la diferencia es de etiqueta, no de datos (los records son los mismos)."""
import sys, io, os, json
from pathlib import Path
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP)); sys.path.insert(0, str(SNAP / "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp, referencia_mirova_unificada as rmu
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
V = ("2026-03-01", "2026-10-21"); coords = _coords_por_volcan()
TABLA = SNAP / "latest_consolidado.csv"; OCR = SNAP / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
comb = rmu.cargar_referencia_unificada(TABLA, OCR, respaldo_path=None, historico_path=None)
refs = {"S158": rmu.cargar_referencia_unificada(), "comb": comb, "tabla": [f for f in comb if f["source"] == "CONS"]}
base = []
for vol in bp.VOLS:
    for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None or not (V[0] <= r.get("datetime_utc", "")[:10] <= V[1]): continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if es_pasada_diurna_descartada(b, *coords[vol], dt): continue
        base.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "nti": r.get("diag_nti_max"), "sensor": r["sensor"]})
lab = {}
for k, f in refs.items():
    recs = [dict(x) for x in base]
    bp.etiquetar(recs, *bp.indexar_referencia(f, coords, V, regla_minimas="SN")[:3])
    lab[k] = recs
for i, r in enumerate(lab["tabla"]):
    if r["lab"] == "neg_limpio" and r["nti"] is not None and r["nti"] > -0.87:
        print(r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"), "nti_max", r["nti"], "| etiqueta S158:", lab["S158"][i]["lab"], "| comb:", lab["comb"][i]["lab"])
        for f in refs["S158"]:
            if f["volcano"] == r["vol"] and f["fecha_utc"][:10] == r["noche"] and f["sensor_bucket"] == r["b"]:
                print("     ref S158:", {k: f.get(k) for k in ("fecha_utc", "source", "origen", "vrp_mw", "dist_km", "tipo")})
