"""F2.6.h — Lascar lost summit >500 MW records (S26 -> S71) vs MIROVA NRT (CONS+OCR).

Identify S26 records (vrp_mw > 500 MW, distance_class=summit) NOT present in S71,
then cross-check against MIROVA NRT consolidado + OCR registries to verify whether
they were real TPs that S40+S46 cluster aggregation may have lost.

Read-only. Convention A4: pc.vrp_mw style — but at record level we use
record.vrp_mw since both S26 and S71 are record-level extracts.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
S26_PATH = ROOT.parent / "135_lascar_lost_records_vs_tifs" / "Lascar_S26.json"
S71_PATH = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/data/mirova_equivalent/Lascar.json")
CONS_CSV = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
OCR_CSV = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/data/mirova_reference/registro_vrp_ocr.csv")
LASCAR_CSV = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/data/mirova_reference/mirova_v1_snapshot/registro_Lascar.csv")

# Threshold for filter
SUMMIT_VRP_MIN = 500.0


def parse_dt(s):
    if not s:
        return None
    s = s.replace("T", " ").split("+")[0].split(".")[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def sensor_canon_s26(s):
    if not s:
        return None
    u = s.upper()
    if "MODIS" in u:
        return "MODIS"
    if "VIIRS" in u and ("375" in u or "I04" in u or "_I" in u):
        return "VIIRS375"
    if "VIIRS" in u:
        return "VIIRS750"
    return u


def sensor_canon_mirova(s):
    if not s:
        return None
    u = s.upper().strip()
    if "MODIS" in u:
        return "MODIS"
    if "VIIRS375" in u or "375" in u:
        return "VIIRS375"
    if "VIIRS" in u:  # MIROVA NRT VIIRS = 750m generally
        return "VIIRS750"
    return u


def load_mirova_records():
    """Load Lascar rows from CONS + OCR + per-vol CSV. Return list of dicts."""
    rows = []
    sources = [
        (CONS_CSV, "CONS"),
        (OCR_CSV, "OCR"),
        (LASCAR_CSV, "LASCAR_SPECIFIC"),
    ]
    for path, src in sources:
        if not path.exists():
            print(f"WARN missing: {path}")
            continue
        with path.open(encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                vol = (row.get("Volcan") or "").strip()
                if "lascar" not in vol.lower():
                    continue
                dt = parse_dt(row.get("Fecha_Satelite_UTC"))
                if dt is None:
                    continue
                try:
                    vrp = float(row.get("VRP_MW") or 0)
                except ValueError:
                    vrp = 0.0
                try:
                    dist = float(row.get("Distancia_km") or 0)
                except ValueError:
                    dist = 0.0
                rows.append({
                    "dt": dt,
                    "sensor_canon": sensor_canon_mirova(row.get("Sensor")),
                    "sensor_raw": row.get("Sensor"),
                    "vrp_mw": vrp,
                    "dist_km": dist,
                    "tipo": (row.get("Tipo_Registro") or "").strip(),
                    "clasif": (row.get("Clasificacion Mirova") or "").strip(),
                    "src": src,
                })
    return rows


def match_mirova(target_dt, target_sensor_canon, mirova_rows, window_min=60):
    """Find best MIROVA row matching target within +/- window_min minutes.
    Same sensor canon preferred; if none, fallback to any same-day match.
    Returns list of matches (could be multiple)."""
    target_w = timedelta(minutes=window_min)
    same_sensor = []
    any_sensor_sameday = []
    for r in mirova_rows:
        if r["sensor_canon"] == target_sensor_canon:
            delta = abs((r["dt"] - target_dt).total_seconds())
            if delta <= target_w.total_seconds():
                same_sensor.append((delta, r))
        # also collect same-day any sensor for fallback
        if r["dt"].date() == target_dt.date():
            any_sensor_sameday.append(r)
    same_sensor.sort(key=lambda x: x[0])
    return same_sensor, any_sensor_sameday


def classify_verdict(matches_same_sensor, sameday_any):
    """Classify what MIROVA NRT said about this time-slot.
    Return (verdict, evidence_row)."""
    if matches_same_sensor:
        # take the closest
        best = matches_same_sensor[0][1]
        tipo = best["tipo"]
        if tipo == "ALERTA_TERMICA":
            return "MIROVA_ALERTA", best
        if tipo == "FALSO_POSITIVO":
            return "MIROVA_FALSO_POSITIVO", best
        if tipo == "RUTINA":
            return "MIROVA_RUTINA", best  # MIROVA said nothing happening
        return f"MIROVA_OTHER_{tipo}", best
    # no same-sensor in window; check same-day for context
    alertas = [r for r in sameday_any if r["tipo"] == "ALERTA_TERMICA"]
    if alertas:
        return "SAMEDAY_ALERTA_DIFFSENSOR", alertas[0]
    if sameday_any:
        # we have data for that day but no alert in window
        return "SAMEDAY_NO_ALERT", sameday_any[0]
    return "NO_MIROVA_DATA", None


def main():
    print("Loading S26 + S71...")
    s26 = json.loads(S26_PATH.read_text())
    s71 = json.loads(S71_PATH.read_text())
    s26_recs = s26["records"]
    s71_recs = s71["records"]
    print(f"S26: {len(s26_recs)} | S71: {len(s71_recs)}")

    # Build S71 index — sensor_canon + 5-min bucket
    def bucket_key(dt, canon):
        if not dt:
            return None
        minute = (dt.minute // 5) * 5
        b = dt.replace(minute=minute, second=0, microsecond=0)
        return (canon, b)

    s71_idx = {}
    for r in s71_recs:
        dt = parse_dt(r.get("datetime_utc"))
        canon = sensor_canon_s26(r.get("sensor"))
        k = bucket_key(dt, canon)
        if k:
            s71_idx[k] = r

    # Filter S26: lost + summit + vrp>500
    candidates = []
    for r in s26_recs:
        vrp = r.get("vrp_mw") or 0
        if vrp <= SUMMIT_VRP_MIN:
            continue
        if r.get("distance_class") != "summit":
            continue
        dt = parse_dt(r.get("datetime_utc"))
        canon = sensor_canon_s26(r.get("sensor"))
        k = bucket_key(dt, canon)
        s71_r = s71_idx.get(k)
        # try ±5,10 min
        if s71_r is None and k:
            for delta in (-5, 5, -10, 10):
                alt = (k[0], k[1] + timedelta(minutes=delta))
                if alt in s71_idx:
                    s71_r = s71_idx[alt]
                    break
        s71_vrp = (s71_r.get("vrp_mw") or 0) if s71_r else None
        if s71_r is not None and s71_vrp > 0.01:
            continue  # not lost
        candidates.append({
            "datetime_utc": r.get("datetime_utc"),
            "sensor": r.get("sensor"),
            "sensor_canon": canon,
            "s26_vrp_mw": vrp,
            "s26_dist_km": r.get("final_hotspot_dist_km"),
            "s26_class": r.get("distance_class"),
            "s26_n_pixels": r.get("n_anomalous_pixels"),
            "s26_t_max_k": r.get("t_max_k"),
            "_dt": dt,
        })
    print(f"Lost summit vrp>{SUMMIT_VRP_MIN} candidates: {len(candidates)}")

    # Load MIROVA NRT rows
    print("Loading MIROVA NRT CONS + OCR + LASCAR_SPECIFIC...")
    mirova_rows = load_mirova_records()
    print(f"MIROVA Lascar rows total (all sources): {len(mirova_rows)}")
    print(f"  ALERTA_TERMICA: {sum(1 for r in mirova_rows if r['tipo']=='ALERTA_TERMICA')}")
    print(f"  FALSO_POSITIVO: {sum(1 for r in mirova_rows if r['tipo']=='FALSO_POSITIVO')}")
    print(f"  RUTINA: {sum(1 for r in mirova_rows if r['tipo']=='RUTINA')}")

    # Classify each candidate
    verdict_counts = {}
    detailed = []
    for c in candidates:
        same_sensor, sameday = match_mirova(c["_dt"], c["sensor_canon"], mirova_rows, window_min=60)
        verdict, ev = classify_verdict(same_sensor, sameday)
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        entry = dict(c)
        entry["verdict"] = verdict
        entry["n_same_sensor_within_60min"] = len(same_sensor)
        if ev:
            entry["mirova_dt"] = ev["dt"].isoformat()
            entry["mirova_sensor"] = ev["sensor_raw"]
            entry["mirova_vrp_mw"] = ev["vrp_mw"]
            entry["mirova_dist_km"] = ev["dist_km"]
            entry["mirova_tipo"] = ev["tipo"]
            entry["mirova_clasif"] = ev["clasif"]
            entry["mirova_src"] = ev["src"]
            if ev["vrp_mw"] > 0 and c["s26_vrp_mw"] > 0:
                entry["s26_over_mirova_ratio"] = c["s26_vrp_mw"] / ev["vrp_mw"]
        entry.pop("_dt", None)
        detailed.append(entry)

    # Summary
    print("\n=== VERDICT DISTRIBUTION ===")
    total = len(candidates)
    for v, n in sorted(verdict_counts.items(), key=lambda x: -x[1]):
        print(f"  {v:35s}: {n:3d} ({100*n/max(total,1):.1f}%)")

    # Sub-analysis: MIROVA_ALERTA matches — were they inflated?
    alertas = [d for d in detailed if d["verdict"] == "MIROVA_ALERTA"]
    print(f"\n=== MIROVA_ALERTA matches: {len(alertas)} ===")
    if alertas:
        ratios = [d.get("s26_over_mirova_ratio") for d in alertas if d.get("s26_over_mirova_ratio")]
        if ratios:
            ratios_sorted = sorted(ratios)
            n = len(ratios_sorted)
            median = ratios_sorted[n//2]
            print(f"  Ratio S26/MIROVA: median={median:.2f}× min={min(ratios):.2f}× max={max(ratios):.2f}×")
            print(f"  ratio>5× (inflated): {sum(1 for r in ratios if r>5)}")
            print(f"  ratio>10× (very inflated): {sum(1 for r in ratios if r>10)}")
            print(f"  ratio 0.5-2 (calibrated): {sum(1 for r in ratios if 0.5<=r<=2)}")
        print("\n  First 15 MIROVA_ALERTA cases:")
        for d in alertas[:15]:
            print(f"    {d['datetime_utc']} {d['sensor']:18s} S26={d['s26_vrp_mw']:.1f}MW MIROVA={d.get('mirova_vrp_mw',0):.2f}MW ratio={d.get('s26_over_mirova_ratio',0):.1f}× tipo={d.get('mirova_tipo')}")

    # Save JSON
    out = {
        "summary": {
            "s26_records": len(s26_recs),
            "s71_records": len(s71_recs),
            "summit_vrp_min_mw": SUMMIT_VRP_MIN,
            "candidates_total": total,
            "verdict_counts": verdict_counts,
            "mirova_rows_loaded": len(mirova_rows),
        },
        "candidates": detailed,
    }
    out_path = ROOT / "audit.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
