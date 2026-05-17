"""S48 VIIRS-DEEP — per-volcano VIIRS-I 375m performance audit, 30d window.

Window: 2026-04-16 -> 2026-05-16.
Tier A volcanoes (11). For each volcano:
  - VIIRS-I records (sensor starts with VIIRS_ and does NOT end with _750), pc_vrp>0
  - summit/far split by inner_radius_km
  - sub-MW vs above-MW
  - MIROVA NRT CSV cross-reference (VIIRS375 sensor) for same window
  - recall: ours detected within +/-30min of MIROVA ALERTA_TERMICA
Output: table + JSON for downstream.
"""
from __future__ import annotations
import json
import csv
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/nostalgic-aryabhata-e05d1e")
DATA_DIR = REPO / "data" / "mirova_equivalent"
CSV_PATH = REPO / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OUT_JSON = REPO / "experiments" / "91_viirs_per_vol_deep.json"
OUT_MD = REPO / "experiments" / "91_viirs_per_vol_deep.md"

WIN_START = datetime(2026, 4, 16, tzinfo=timezone.utc)
WIN_END = datetime(2026, 5, 16, 23, 59, 59, tzinfo=timezone.utc)

# Tier A: name in mirova_equivalent JSON -> (csv_name, inner_radius_km)
TIER_A = {
    "PuyehueCordonCaulle": ("Puyehue-Cordon Caulle", 20),
    "Villarrica": ("Villarrica", 5),
    "Lascar": ("Lascar", 5),
    "Copahue": ("Copahue", 4),
    "NevadosDeChillan": ("Nevados de Chillan", 5),
    "Llaima": ("Llaima", 5),
    "Chaiten": ("Chaiten", 5),
    "PlanchonPeteroa": ("Planchon-Peteroa", 3),
    "Lastarria": ("Lastarria", 3),
    "Isluga": ("Isluga", 5),
    "Tupungatito": ("Tupungatito", 7),
}


def parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    try:
        # ISO Z
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        if "T" in s:
            d = datetime.fromisoformat(s)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d
        # CSV: "2026-05-16 21:30:00"  or  JSON record: "2026-01-29 02:35"
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def is_viirs_i(sensor: str) -> bool:
    if not sensor:
        return False
    return sensor.startswith("VIIRS_") and not sensor.endswith("_750")


def is_viirs_m(sensor: str) -> bool:
    return bool(sensor) and sensor.startswith("VIIRS_") and sensor.endswith("_750")


def is_modis(sensor: str) -> bool:
    return bool(sensor) and sensor.startswith("MODIS_")


def load_csv_alerts():
    """Return dict[vol_csv_name] -> list of dicts {dt, sensor, vrp_mw, tipo, clas}."""
    out = defaultdict(list)
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for row in rd:
            dt = parse_dt(row.get("Fecha_Satelite_UTC", ""))
            if not dt or not (WIN_START <= dt <= WIN_END):
                continue
            vol = row.get("Volcan", "").strip()
            sensor = row.get("Sensor", "").strip()
            try:
                vrp = float(row.get("VRP_MW", 0) or 0)
            except Exception:
                vrp = 0.0
            out[vol].append({
                "dt": dt,
                "sensor": sensor,
                "vrp_mw": vrp,
                "tipo": row.get("Tipo_Registro", "").strip(),
                "clas": row.get("Clasificacion Mirova", "").strip(),
            })
    return out


def analyze_volcano(vol_key: str, csv_name: str, inner_km: float, csv_alerts):
    fp = DATA_DIR / f"{vol_key}.json"
    if not fp.exists():
        return None
    data = json.loads(fp.read_text(encoding="utf-8"))
    recs = data.get("records", [])

    # Per-sensor buckets
    buckets = {"VIIRS_I": [], "VIIRS_M": [], "MODIS": []}
    for r in recs:
        dt = parse_dt(r.get("datetime_utc", ""))
        if not dt or not (WIN_START <= dt <= WIN_END):
            continue
        pc = r.get("primary_cluster") or {}
        pc_vrp = pc.get("vrp_mw") or 0
        if pc_vrp <= 0:
            continue
        s = r.get("sensor", "")
        if is_viirs_i(s):
            buckets["VIIRS_I"].append(r)
        elif is_viirs_m(s):
            buckets["VIIRS_M"].append(r)
        elif is_modis(s):
            buckets["MODIS"].append(r)

    # Stats per sensor
    def sensor_stats(records):
        if not records:
            return {"n": 0, "n_summit": 0, "n_far": 0, "n_sub_mw": 0, "n_above_mw": 0,
                    "median_pc_vrp": 0.0, "far_ratio": 0.0}
        summit = far = sub = above = 0
        vrps = []
        for r in records:
            pc = r.get("primary_cluster") or {}
            d = pc.get("centroid_dist_km")
            if d is None:
                d = pc.get("dist_km")
            if d is None:
                d = r.get("final_hotspot_dist_km")
            v = pc.get("vrp_mw") or 0
            vrps.append(v)
            if d is not None and d <= inner_km:
                summit += 1
            else:
                far += 1
            if v < 1.0:
                sub += 1
            else:
                above += 1
        return {
            "n": len(records),
            "n_summit": summit,
            "n_far": far,
            "n_sub_mw": sub,
            "n_above_mw": above,
            "median_pc_vrp": round(median(vrps), 3) if vrps else 0.0,
            "far_ratio": round(far / len(records), 3),
        }

    stats = {k: sensor_stats(v) for k, v in buckets.items()}

    # MIROVA CSV cross-reference for VIIRS375
    csv_rows = csv_alerts.get(csv_name, [])
    viirs375_csv = [r for r in csv_rows if r["sensor"] == "VIIRS375"]
    n_alerta = sum(1 for r in viirs375_csv if r["tipo"] == "ALERTA_TERMICA")
    n_rutina = sum(1 for r in viirs375_csv if r["tipo"] == "RUTINA")
    n_fp_csv = sum(1 for r in viirs375_csv if r["tipo"] == "FALSO_POSITIVO")

    # Recall: VIIRS_I records within +-30min of ALERTA_TERMICA VIIRS375
    alertas = [r["dt"] for r in viirs375_csv if r["tipo"] == "ALERTA_TERMICA"]
    matched = 0
    for a_dt in alertas:
        hit = False
        for r in buckets["VIIRS_I"]:
            r_dt = parse_dt(r.get("datetime_utc", ""))
            if r_dt and abs((r_dt - a_dt).total_seconds()) <= 1800:
                hit = True
                break
        if hit:
            matched += 1
    recall = (matched / n_alerta) if n_alerta else None

    return {
        "volcano": vol_key,
        "inner_radius_km": inner_km,
        "csv_viirs375": {"n_alerta": n_alerta, "n_rutina": n_rutina, "n_fp": n_fp_csv},
        "viirs_i_recall": recall,
        "viirs_i_matched": matched,
        "sensors": stats,
    }


def main():
    csv_alerts = load_csv_alerts()
    results = []
    for vol_key, (csv_name, inner) in TIER_A.items():
        r = analyze_volcano(vol_key, csv_name, inner, csv_alerts)
        if r:
            results.append(r)

    OUT_JSON.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    # Markdown report
    lines = []
    lines.append("# S48 VIIRS-DEEP per-volcano analysis (30d 2026-04-16 -> 2026-05-16)\n")
    lines.append("## Tabla VIIRS-I 375m por volcán\n")
    lines.append("| Volcán | inner_km | n_alertas_MIROVA | recall_VIIRS-I | n_summit | n_far | far_ratio | n_sub_MW | n_above_MW | med_pc_vrp |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        vi = r["sensors"]["VIIRS_I"]
        rec = "—" if r["viirs_i_recall"] is None else f"{r['viirs_i_recall']*100:.0f}% ({r['viirs_i_matched']}/{r['csv_viirs375']['n_alerta']})"
        lines.append(f"| {r['volcano']} | {r['inner_radius_km']} | {r['csv_viirs375']['n_alerta']} | {rec} | {vi['n_summit']} | {vi['n_far']} | {vi['far_ratio']:.2f} | {vi['n_sub_mw']} | {vi['n_above_mw']} | {vi['median_pc_vrp']} |")

    lines.append("\n## Comparativa per-sensor (n records con pc_vrp>0)\n")
    lines.append("| Volcán | MODIS | VIIRS-M 750 | VIIRS-I 375 | % VIIRS-I del total |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in results:
        nM = r["sensors"]["MODIS"]["n"]; nVM = r["sensors"]["VIIRS_M"]["n"]; nVI = r["sensors"]["VIIRS_I"]["n"]
        tot = nM + nVM + nVI
        pct = (nVI / tot * 100) if tot else 0
        lines.append(f"| {r['volcano']} | {nM} | {nVM} | {nVI} | {pct:.0f}% |")

    lines.append("\n## Medianas pc_vrp por sensor\n")
    lines.append("| Volcán | MODIS_med | VIIRS-M_med | VIIRS-I_med |")
    lines.append("|---|---:|---:|---:|")
    for r in results:
        lines.append(f"| {r['volcano']} | {r['sensors']['MODIS']['median_pc_vrp']} | {r['sensors']['VIIRS_M']['median_pc_vrp']} | {r['sensors']['VIIRS_I']['median_pc_vrp']} |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nJSON: {OUT_JSON}")
    print(f"MD:   {OUT_MD}")


if __name__ == "__main__":
    main()
