"""S99 — Núcleo F5' vs Cluster: ¿cuál se asemeja MÁS a MIROVA? POR SENSOR.

Pregunta de Nicolás: entre la magnitud "Cluster" (primary_cluster.vrp_mw crudo)
y el "Núcleo F5'" (recorte al pico de energía, frontend/index.html
f5CoreMagnitude), ¿cuál se parece más a lo que MIROVA publica, y tiene sentido
mantener las dos? Respuesta POR SENSOR (MODIS / VIIRS375 / VIIRS750).

Reutiliza la lógica de matching MIROVA↔nuestro de
experiments/_s98_anchor/audit_ratio.py (CONS+OCR, ±15 min, familia de sensor,
A14 alias de nombres, A10 pc.vrp_mw).

Núcleo: replica EXACTO mirovaEqVrpCore + f5CoreMagnitude de frontend/index.html
(commit actual). Reglas reproducidas verbatim:
  - F5_R_CORE_KM = 0.75, F5_BT_EXT_K = 295.0
  - SOLO se aplica a VIIRS375 (I-band, sensor empieza con VIIRS y NO termina en
    _750). MODIS / VIIRS750 → núcleo = cluster (base).
  - base = mirovaEqVrp(r, innerKm): si dist_class != summit → 0; si
    centroid_dist_km > innerKm → 0; si no, pc.vrp_mw (cap 50000).
  - f5CoreMagnitude: candidatos = anomaly_pixels con lat/lon dentro de innerKm
    del centroide del cluster; pico = píxel de MÁXIMA vrp_mw; suma = pico +
    píxeles a <=0.75 km del pico + píxeles con bt_k>=295. Si no hay candidatos
    → None → fallback a base.
  - Guard S96: si core==None o core<=0 con base>0 → usar base (nunca borra).
  - cap final: core>50000 → 0.

NO usa el toggle includeFar (default false, como el dashboard operacional).
innerKm = inner_radius_km del volcán (de frontend/index.html).

A48: convención de sensor verificada, NO regex inventada.
S91/integridad: ningún número a mano; todo de este script.
"""
import csv
import json
import math
import statistics as st
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
WIN_START = datetime(2026, 5, 1)
WIN_END = datetime(2026, 5, 18, 23, 59, 59)  # snapshot CONS llega a 05-18

CSV_BASE = _REPO / "data/mirova_reference/mirova_v1_snapshot"
CSV_CONS = CSV_BASE / "registro_vrp_consolidado.csv"
CSV_OCR = CSV_BASE / "registro_vrp_ocr.csv"

F5_R_CORE_KM = 0.75
F5_BT_EXT_K = 295.0

# Los 11 Tier A: (nuestro_nombre_json, nombre_en_CSV, inner_radius_km)
# inner_radius_km tomado de frontend/index.html (KML oficial MIROVA).
# A14: variantes de nombre del scraper Mirova-v1.
TIER_A = [
    ("Isluga", "Isluga", 5),
    ("Lascar", "Lascar", 5),
    ("Lastarria", "Lastarria", 3),
    ("Tupungatito", "Tupungatito", 7),
    ("PlanchonPeteroa", "PlanchonPeteroa", 3),
    ("NevadosDeChillan", "Nevados de Chillan", 5),
    ("Copahue", "Copahue", 4),
    ("Llaima", "Llaima", 5),
    ("Villarrica", "Villarrica", 5),
    ("PuyehueCordonCaulle", "Puyehue-Cordon Caulle", 20),
    ("Chaiten", "Chaiten", 5),
]
# "Peteroa" (65 filas CONS) es alias adicional de PlanchonPeteroa en el CSV.
EXTRA_CSV = {"PlanchonPeteroa": ["Peteroa"]}


def sensor_family(s):
    s = s or ""
    if "MODIS" in s:
        return "MODIS"
    if "750" in s:
        return "VIIRS750"
    if "VIIRS" in s:
        return "VIIRS375"
    return s


def is_viirs375(sensor):
    """Replica el gate de mirovaEqVrpCore: VIIRS y NO _750."""
    s = str(sensor or "").upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def hav_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    rad = math.pi / 180
    p1, p2 = lat1 * rad, lat2 * rad
    dp = (lat2 - lat1) * rad
    dl = (lon2 - lon1) * rad
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_refs(path, vol_csv_names, types):
    refs = []
    if not Path(path).exists():
        return refs
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Volcan") not in vol_csv_names:
                continue
            if row.get("Tipo_Registro") not in types:
                continue
            try:
                dt = datetime.strptime(row["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                continue
            if not (WIN_START <= dt <= WIN_END):
                continue
            try:
                vrp = float(row["VRP_MW"])
            except (ValueError, KeyError):
                continue
            refs.append({"dt": dt, "sensor": row.get("Sensor", ""), "vrp": vrp})
    return refs


def load_our(name):
    p = _REPO / "data" / "mirova_equivalent" / f"{name}.json"
    if not p.exists():
        return []
    d = json.load(open(p, encoding="utf-8"))
    return d if isinstance(d, list) else d.get("records", [])


def mirova_eq_vrp(rec, inner_km, include_far=False):
    """Replica frontend mirovaEqVrp (base)."""
    if not rec:
        return 0.0
    pc = rec.get("primary_cluster")
    if not pc:
        vfb = rec.get("vrp_mw")
        if vfb is None:
            vfb = rec.get("vrp_mir_mw") or 0
        return 0.0 if vfb > 50000 else vfb
    dc = rec.get("distance_class")
    if dc and dc != "summit" and not include_far:
        return 0.0
    cd = pc.get("centroid_dist_km")
    if not include_far and cd is not None and cd > inner_km:
        return 0.0
    vmw = pc.get("vrp_mw") or 0
    return 0.0 if vmw > 50000 else vmw


def f5_core_magnitude(rec, inner_km):
    """Replica frontend f5CoreMagnitude. Devuelve None si no recomputable."""
    pixels = rec.get("anomaly_pixels")
    if not pixels:
        return None
    pc = rec.get("primary_cluster")
    if not pc or pc.get("centroid_lat") is None or pc.get("centroid_lon") is None:
        return None
    clat, clon = pc["centroid_lat"], pc["centroid_lon"]
    cand = [p for p in pixels
            if p.get("lat") is not None and p.get("lon") is not None
            and hav_km(p["lat"], p["lon"], clat, clon) <= inner_km]
    if not cand:
        return None
    peak = 0
    for i in range(1, len(cand)):
        if (cand[i].get("vrp_mw") or 0) > (cand[peak].get("vrp_mw") or 0):
            peak = i
    plat, plon = cand[peak].get("lat"), cand[peak].get("lon")
    if plat is None or plon is None:
        return None
    total = 0.0
    for i, p in enumerate(cand):
        keep = (i == peak) \
            or (p.get("lat") is not None and p.get("lon") is not None
                and hav_km(p["lat"], p["lon"], plat, plon) <= F5_R_CORE_KM) \
            or ((p.get("bt_k") or 0) >= F5_BT_EXT_K)
        if keep:
            total += (p.get("vrp_mw") or 0)
    return total


def mirova_eq_vrp_core(rec, inner_km, include_far=False):
    """Replica frontend mirovaEqVrpCore: núcleo SOLO en VIIRS375, con guards."""
    base = mirova_eq_vrp(rec, inner_km, include_far)
    if base <= 0:
        return base
    if not is_viirs375(rec.get("sensor")):
        return base  # MODIS / VIIRS750 conservan el cluster
    core = f5_core_magnitude(rec, inner_km)
    if core is None or core <= 0:
        return base  # guard S96: nunca borra
    return 0.0 if core > 50000 else core


def match_records(refs, recs, inner_km):
    """Para cada ALERTA MIROVA, elige nuestro record (centroide más cercano) y
    devuelve filas con cluster_vrp, nucleo_vrp, mirova_vrp, sensor_family."""
    rows = []
    for r in refs:
        cands = []
        for rec in recs:
            try:
                rdt = datetime.fromisoformat(str(rec["datetime_utc"]).replace("Z", ""))
            except (ValueError, KeyError):
                continue
            if abs((rdt - r["dt"]).total_seconds()) > 900:
                continue
            if sensor_family(rec.get("sensor", "")) != sensor_family(r["sensor"]):
                continue
            cands.append(rec)
        if not cands:
            continue
        best = min(cands, key=lambda x: (x.get("primary_cluster") or {}).get("centroid_dist_km", 99))
        cluster_vrp = mirova_eq_vrp(best, inner_km)   # base = pc.vrp_mw filtrado igual que display
        if cluster_vrp <= 0:
            continue  # MIROVA reportó pero nosotros no (no detectado / lejano): sin ratio
        nucleo_vrp = mirova_eq_vrp_core(best, inner_km)
        if r["vrp"] <= 0:
            continue
        rows.append({
            "sensor_family": sensor_family(best.get("sensor", "")),
            "mirova_vrp": r["vrp"],
            "cluster_vrp": cluster_vrp,
            "nucleo_vrp": nucleo_vrp,
            "ratio_cluster": cluster_vrp / r["vrp"],
            "ratio_nucleo": nucleo_vrp / r["vrp"],
        })
    return rows


def band(ratios):
    return round(100 * sum(1 for x in ratios if 0.5 <= x <= 2.0) / len(ratios), 1) if ratios else None


def stats(ratios):
    if not ratios:
        return {"n": 0}
    return {
        "n": len(ratios),
        "median": round(st.median(ratios), 3),
        "min": round(min(ratios), 3),
        "max": round(max(ratios), 3),
        "pct_in_band": band(ratios),
    }


def main():
    all_rows = []
    per_vol = {}
    for our, csvn, inner in TIER_A:
        csv_names = [csvn] + EXTRA_CSV.get(our, [])
        refs = (load_refs(CSV_CONS, csv_names, ["ALERTA_TERMICA"]) +
                load_refs(CSV_OCR, csv_names, ["ALERTA_TERMICA_OCR"]))
        recs = load_our(our)
        rows = match_records(refs, recs, inner)
        for row in rows:
            row["volcano"] = our
        all_rows.extend(rows)
        per_vol[our] = rows

    # Agregado por sensor (global)
    by_sensor = {}
    for sf in ("MODIS", "VIIRS375", "VIIRS750"):
        sub = [x for x in all_rows if x["sensor_family"] == sf]
        by_sensor[sf] = {
            "cluster": stats([x["ratio_cluster"] for x in sub]),
            "nucleo": stats([x["ratio_nucleo"] for x in sub]),
        }
    by_sensor["TOTAL"] = {
        "cluster": stats([x["ratio_cluster"] for x in all_rows]),
        "nucleo": stats([x["ratio_nucleo"] for x in all_rows]),
    }

    # Agregado por volcán (todos los sensores juntos) + desglose VIIRS375
    by_vol = {}
    for our, _, _ in TIER_A:
        rows = per_vol[our]
        v375 = [x for x in rows if x["sensor_family"] == "VIIRS375"]
        by_vol[our] = {
            "n_matched": len(rows),
            "all": {
                "cluster": stats([x["ratio_cluster"] for x in rows]),
                "nucleo": stats([x["ratio_nucleo"] for x in rows]),
            },
            "viirs375_only": {
                "cluster": stats([x["ratio_cluster"] for x in v375]),
                "nucleo": stats([x["ratio_nucleo"] for x in v375]),
            },
        }

    out = {
        "window": f"{WIN_START.date()}..{WIN_END.date()}",
        "n_records_matched": len(all_rows),
        "by_sensor": by_sensor,
        "by_volcano": by_vol,
    }
    outp = _REPO / "experiments/_s99_audit/nucleo_vs_cluster_result.json"
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return out


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    out = main()
    print(json.dumps(out, indent=2, ensure_ascii=False))
