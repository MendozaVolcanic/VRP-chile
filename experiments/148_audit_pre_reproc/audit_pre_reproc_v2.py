"""S77 audit pre-reproc v2 — CORRECCIÓN del bucketing sensor (PR #196 bug).

Bug v1: `sensor_bucket_ours("VIIRS_SNPP")` retornaba "VIIRS" (M-band) porque
el regex no detectaba I-band en la convención real:
- I-band 375m: VIIRS_SNPP, VIIRS_NOAA20, VIIRS_NOAA21 (sin sufijo)
- M-band 750m: VIIRS_SNPP_750, VIIRS_NOAA20_750, VIIRS_NOAA21_750
- MODIS:       MODIS_AQUA, MODIS_TERRA

V2 fix: ends_with('_750') → 'VIIRS' (M-band MIROVA naming),
        startswith('VIIRS_') sin _750 → 'VIIRS375',
        startswith('MODIS_') → 'MODIS'.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TIER_A = ("Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima",
          "NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle",
          "Tupungatito","Villarrica")
NORM = {"Nevados de Chillan":"NevadosDeChillan",
        "Puyehue-Cordon Caulle":"PuyehueCordonCaulle",
        "Planchon-Peteroa":"PlanchonPeteroa"}


def parse_dt(s):
    if not s: return None
    try: return datetime.fromisoformat(s.replace(" ","T"))
    except: return None


def sensor_bucket_ours_v2(sensor: str) -> str:
    """Fix v2: correctly map our sensor strings to MIROVA buckets."""
    if not sensor: return "UNKNOWN"
    s = sensor.upper()
    if s.startswith("MODIS_") or s == "MODIS": return "MODIS"
    if s.endswith("_750"): return "VIIRS"           # M-band 750m
    if s.startswith("VIIRS_"): return "VIIRS375"    # I-band 375m
    return "UNKNOWN"


def inner_radius_km(volcano: str) -> float:
    """Carga inner_radius desde volcanoes.yaml."""
    import yaml
    cfg = yaml.safe_load(open(REPO / "volcanoes.yaml", "r", encoding="utf-8"))
    for v in cfg["volcanoes"]:
        if v["name"] == volcano:
            return float(v.get("inner_radius_km", 10))
    return 10.0


def mirova_eq_vrp(rec: dict, inner_km: float) -> float:
    """Replica mirovaEqVrp del frontend."""
    pc = rec.get("primary_cluster") or {}
    pc_vrp = pc.get("vrp_mw") or 0
    if pc_vrp <= 0: return 0
    if rec.get("distance_class") != "summit": return 0
    pc_dist = pc.get("centroid_dist_km")
    if pc_dist is not None and pc_dist > inner_km: return 0
    return float(pc_vrp)


# Load MIROVA records (CSV consolidado fresh post-F49)
print("=== Loading MIROVA CSV ===")
mir_records = []
with open(REPO / "latest_consolidado.csv", "r", encoding="utf-8") as fp:
    for row in csv.DictReader(fp):
        v = NORM.get(row.get("Volcan",""), row.get("Volcan",""))
        if v not in TIER_A: continue
        try: vrp = float(row.get("VRP_MW") or 0)
        except: continue
        dt = parse_dt(row.get("Fecha_Satelite_UTC"))
        if not dt: continue
        mir_records.append({
            "volcano": v, "dt": dt, "sensor": row.get("Sensor",""),
            "vrp": vrp, "clasif": row.get("Clasificacion Mirova","NULO"),
        })
print(f"  MIROVA records {len(TIER_A)} Tier A: {len(mir_records)}")
mir_last = max(r["dt"] for r in mir_records)
print(f"  MIROVA latest: {mir_last.isoformat()}")

# Load OCR (alertas reales gráficas) — complemento
ocr_records = []
ocr_path = REPO / "data" / "mirova_reference" / "registro_vrp_ocr.csv"
if ocr_path.exists():
    with open(ocr_path, "r", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            v = NORM.get(row.get("Volcan",""), row.get("Volcan",""))
            if v not in TIER_A: continue
            try: vrp = float(row.get("VRP_MW") or 0)
            except: continue
            dt = parse_dt(row.get("Fecha_Satelite_UTC"))
            if not dt: continue
            ocr_records.append({
                "volcano": v, "dt": dt, "sensor": row.get("Sensor",""),
                "vrp": vrp, "clasif": row.get("Clasificacion Mirova","OCR"),
            })
    print(f"  OCR records: {len(ocr_records)}")

# Load nuestros records (post-fixes S77)
print("\n=== Loading OURS ===")
ours_records = []
for vol in TIER_A:
    p = REPO / "data" / "mirova_equivalent" / f"{vol}.json"
    if not p.exists(): continue
    d = json.load(open(p, "r", encoding="utf-8"))
    inner = inner_radius_km(vol)
    for r in d.get("records", []):
        dt = parse_dt(r.get("datetime_utc"))
        if not dt: continue
        eqv = mirova_eq_vrp(r, inner)
        if eqv <= 0: continue
        ours_records.append({
            "volcano": vol, "dt": dt, "sensor": r.get("sensor",""),
            "bucket": sensor_bucket_ours_v2(r.get("sensor","")),
            "vrp": eqv,
        })
print(f"  OURS records vrp>0: {len(ours_records)}")
from collections import Counter
buckets_ours = Counter(r["bucket"] for r in ours_records)
buckets_mir = Counter(r["sensor"] for r in mir_records)
print(f"  buckets ours: {dict(buckets_ours)}")
print(f"  buckets MIROVA: {dict(buckets_mir)}")

# Match temporal ±60 min + mismo bucket
print("\n=== MATCHING + RATIOS (ventana 30d) ===")
from datetime import timedelta
cutoff = mir_last - timedelta(days=30)

print(f"\n{'Volcan':<22} {'Bucket':<10} {'n_ours':>7} {'n_mir':>7} {'matched':>8} {'med':>8} {'p25':>7} {'p75':>7}")
results = []
for vol in sorted(TIER_A):
    for bucket in ("MODIS", "VIIRS375", "VIIRS"):
        o = [r for r in ours_records if r["volcano"]==vol and r["bucket"]==bucket and r["dt"]>=cutoff]
        m = [r for r in mir_records if r["volcano"]==vol and r["sensor"]==bucket
             and r["vrp"]>0 and r["dt"]>=cutoff]
        ratios = []
        for or_ in o:
            best = None
            for mr_ in m:
                if abs((or_["dt"]-mr_["dt"]).total_seconds()) > 3600: continue
                if best is None or abs((or_["dt"]-mr_["dt"]).total_seconds()) < abs((or_["dt"]-best["dt"]).total_seconds()):
                    best = mr_
            if best: ratios.append(or_["vrp"]/best["vrp"])
        if not o and not m: continue
        med = statistics.median(ratios) if ratios else None
        p25 = sorted(ratios)[len(ratios)//4] if len(ratios)>=4 else None
        p75 = sorted(ratios)[3*len(ratios)//4] if len(ratios)>=4 else None
        results.append({"volcano":vol,"bucket":bucket,"n_ours":len(o),"n_mir":len(m),
                        "n_matched":len(ratios),"ratio_med":med,"ratio_p25":p25,"ratio_p75":p75})
        ms = f"{med:.2f}" if med else "—"
        p25s = f"{p25:.2f}" if p25 else "—"
        p75s = f"{p75:.2f}" if p75 else "—"
        print(f"{vol:<22} {bucket:<10} {len(o):>7} {len(m):>7} {len(ratios):>8} {ms:>8} {p25s:>7} {p75s:>7}")

# Save corrected results
out = REPO / "experiments" / "148_audit_pre_reproc"
out.mkdir(parents=True, exist_ok=True)
with open(out / "master_table_v2.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["volcano","bucket","n_ours","n_mir","n_matched",
                                      "ratio_med","ratio_p25","ratio_p75"])
    w.writeheader()
    w.writerows(results)
print(f"\nSaved: {out / 'master_table_v2.csv'}")

# Veredict summary
print("\n=== VEREDICTO POR VOLCAN (mejor bucket, ventana 30d) ===")
print(f"{'Volcan':<22} {'mejor bucket':<14} {'n_matched':>10} {'ratio_med':>10}  veredicto")
for vol in sorted(TIER_A):
    rows = [r for r in results if r["volcano"]==vol and r["n_matched"]>=3]
    if not rows:
        print(f"{vol:<22} {'(sin matches)':<14}")
        continue
    best = max(rows, key=lambda r: r["n_matched"])
    med = best["ratio_med"]
    if 0.5<=med<=2.0: vd="OK"
    elif med>5: vd="OVER (>5x)"
    elif med>2: vd="over (2-5x)"
    elif med<0.5: vd="SUB (<0.5x)"
    else: vd="?"
    print(f"{vol:<22} {best['bucket']:<14} {best['n_matched']:>10} {med:>10.2f}  {vd}")
