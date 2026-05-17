"""S52-VILLARRICA-VIIRS375-AUDIT: VRP-chile vs MIROVA VIIRS-I 375m on Villarrica.

Window: 2026-01-01 .. 2026-05-16 (5 months).

Compares:
- MIROVA consolidated CSV per-month tallies (ALERTA_TERMICA / FALSO_POSITIVO /
  RUTINA / NULO) for sensor VIIRS375
- VRP-chile mirova_equivalent profile detections for VIIRS_NOAA20/21/SNPP
  (375 m I-band, identified by absence of '_750' suffix)
- timestamp matching to compute recall vs MIROVA ALERTAs and over-detection
  rate (our detections without MIROVA counterpart of any kind)

Read-only. No pipeline changes.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
JSON_PATH = ROOT / "data" / "mirova_equivalent" / "Villarrica.json"

WINDOW_START = "2026-01-01"
WINDOW_END = "2026-05-17"  # inclusive end (5 months window)
INNER_RADIUS_KM = 5.0


def is_v375_ours(sensor: str) -> bool:
    return sensor.startswith("VIIRS_") and not sensor.endswith("_750")


def month_key(dt_str: str) -> str:
    return dt_str[:7]  # YYYY-MM


def parse_mirova_dt(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parse_our_dt(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        return None


# -------- Load MIROVA CSV (Villarrica + VIIRS375 only, in window) --------
mirova_rows: list[dict] = []
with CSV_PATH.open(encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        if row.get("Volcan") != "Villarrica":
            continue
        if row.get("Sensor") != "VIIRS375":
            continue
        fdt = row.get("Fecha_Satelite_UTC", "")
        if not fdt:
            continue
        if not (WINDOW_START <= fdt[:10] < WINDOW_END):
            continue
        mirova_rows.append(row)

print(f"MIROVA Villarrica VIIRS375 rows in window: {len(mirova_rows)}")

# Per-month tallies by Tipo_Registro / Clasificacion
mirova_by_month: dict[str, Counter] = defaultdict(Counter)
mirova_alerts: list[dict] = []
for r in mirova_rows:
    m = month_key(r["Fecha_Satelite_UTC"])
    tipo = r.get("Tipo_Registro", "?")
    mirova_by_month[m][tipo] += 1
    if tipo == "ALERTA_TERMICA":
        mirova_alerts.append(r)

print("\nMIROVA Villarrica VIIRS375 per-month (Tipo_Registro):")
header = ["ALERTA_TERMICA", "FALSO_POSITIVO", "RUTINA"]
print(f"  {'Month':<10}", " ".join(f"{h:>16}" for h in header), "  Total")
for m in sorted(mirova_by_month):
    c = mirova_by_month[m]
    vals = [c.get(k, 0) for k in header]
    print(f"  {m:<10}", " ".join(f"{v:>16}" for v in vals), f"  {sum(c.values())}")

print("\nALERTA_TERMICA detail:")
for a in mirova_alerts:
    print(f"  {a['Fecha_Satelite_UTC']}  VRP={a['VRP_MW']:>8} MW  d={a['Distancia_km']:>6} km  Tipo={a['Tipo_Registro']}")

# -------- Load our detections --------
payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
our_records = payload["records"]
our_v375 = [
    r for r in our_records
    if is_v375_ours(r.get("sensor", ""))
    and r.get("datetime_utc", "")[:10] >= WINDOW_START
    and r.get("datetime_utc", "")[:10] < WINDOW_END
]
print(f"\nVRP-chile VIIRS375 records in window: {len(our_v375)}")

# Per-month tallies
ours_by_month: dict[str, Counter] = defaultdict(Counter)
for r in our_v375:
    m = month_key(r["datetime_utc"])
    pc_vrp = (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0
    dist = r.get("final_hotspot_dist_km")
    has_pc = pc_vrp > 0
    summit = dist is not None and dist <= INNER_RADIUS_KM
    very_close = dist is not None and dist <= 1.0
    crater = dist is not None and dist <= 0.5
    ours_by_month[m]["total"] += 1
    if has_pc:
        ours_by_month[m]["pc_vrp>0"] += 1
    if has_pc and summit:
        ours_by_month[m]["summit_pc>0"] += 1
    if has_pc and very_close:
        ours_by_month[m]["d<=1km"] += 1
    if has_pc and crater:
        ours_by_month[m]["d<=0.5km"] += 1

print("\nVRP-chile VIIRS375 per-month detections:")
cols = ["total", "pc_vrp>0", "summit_pc>0", "d<=1km", "d<=0.5km"]
print(f"  {'Month':<10}", " ".join(f"{c:>12}" for c in cols))
for m in sorted(ours_by_month):
    c = ours_by_month[m]
    print(f"  {m:<10}", " ".join(f"{c.get(k, 0):>12}" for k in cols))

# -------- Timestamp matching (tolerance ±10 min) --------
TOL_MIN = 10

def to_minutes(dt: datetime) -> int:
    return int(dt.timestamp() // 60)


# Build index of our V375 records by minute-bucket
our_by_minute: dict[int, list[dict]] = defaultdict(list)
for r in our_v375:
    dt = parse_our_dt(r["datetime_utc"])
    if dt:
        our_by_minute[to_minutes(dt)].append(r)


def find_ours_near(target: datetime, tol_min: int = TOL_MIN) -> list[dict]:
    tmin = to_minutes(target)
    out = []
    for delta in range(-tol_min, tol_min + 1):
        out.extend(our_by_minute.get(tmin + delta, []))
    return out


# Recall vs MIROVA ALERTAs: do we have summit pc.vrp>0 within ±10 min?
print(f"\nRecall vs MIROVA ALERTA_TERMICA (tol ±{TOL_MIN} min, summit pc.vrp>0):")
hits = 0
for a in mirova_alerts:
    dt = parse_mirova_dt(a["Fecha_Satelite_UTC"])
    if not dt:
        continue
    candidates = find_ours_near(dt)
    summit_hit = [
        r for r in candidates
        if (r.get("primary_cluster") or {}).get("vrp_mw", 0) > 0
        and r.get("final_hotspot_dist_km") is not None
        and r["final_hotspot_dist_km"] <= INNER_RADIUS_KM
    ]
    flag = "HIT" if summit_hit else "MISS"
    best = ""
    if summit_hit:
        best_r = max(summit_hit, key=lambda r: (r.get("primary_cluster") or {}).get("vrp_mw", 0))
        pc = best_r["primary_cluster"]
        best = f" ours: pc.vrp={pc['vrp_mw']:.2f} MW  d={best_r['final_hotspot_dist_km']:.2f} km"
    else:
        # show what we did report (if any record)
        any_rec = candidates[:1]
        if any_rec:
            r = any_rec[0]
            pc = r.get("primary_cluster") or {}
            best = f" ours record present: pc.vrp={pc.get('vrp_mw', 0):.2f} d={r.get('final_hotspot_dist_km')}"
        else:
            best = " no record near"
    if summit_hit:
        hits += 1
    print(f"  {a['Fecha_Satelite_UTC']}  MIROVA VRP={a['VRP_MW']} MW d={a['Distancia_km']} km  [{flag}]{best}")

print(f"\nRecall: {hits}/{len(mirova_alerts)} = {100*hits/max(len(mirova_alerts),1):.0f}%")

# -------- Over-detection: our summit detections without MIROVA counterpart --------
# Build minute-bucket index of MIROVA Villarrica VIIRS375 rows
mirova_by_minute: dict[int, list[dict]] = defaultdict(list)
for r in mirova_rows:
    dt = parse_mirova_dt(r["Fecha_Satelite_UTC"])
    if dt:
        mirova_by_minute[to_minutes(dt)].append(r)


def find_mirova_near(target: datetime, tol_min: int = TOL_MIN) -> list[dict]:
    tmin = to_minutes(target)
    out = []
    for delta in range(-tol_min, tol_min + 1):
        out.extend(mirova_by_minute.get(tmin + delta, []))
    return out


our_summit = [
    r for r in our_v375
    if (r.get("primary_cluster") or {}).get("vrp_mw", 0) > 0
    and r.get("final_hotspot_dist_km") is not None
    and r["final_hotspot_dist_km"] <= INNER_RADIUS_KM
]
print(f"\nOur summit detections (pc.vrp>0, d<=5km): {len(our_summit)}")

buckets = Counter()
mw_with = []
mw_without = []
for r in our_summit:
    dt = parse_our_dt(r["datetime_utc"])
    if not dt:
        continue
    near = find_mirova_near(dt)
    if not near:
        buckets["no_mirova_row"] += 1
        mw_without.append((r.get("primary_cluster") or {})["vrp_mw"])
        continue
    tipos = [m.get("Tipo_Registro", "?") for m in near]
    if "ALERTA_TERMICA" in tipos:
        buckets["mirova_ALERTA"] += 1
        mw_with.append((r.get("primary_cluster") or {})["vrp_mw"])
    elif "FALSO_POSITIVO" in tipos:
        buckets["mirova_FP"] += 1
        mw_with.append((r.get("primary_cluster") or {})["vrp_mw"])
    elif "RUTINA" in tipos:
        buckets["mirova_RUTINA"] += 1
        mw_without.append((r.get("primary_cluster") or {})["vrp_mw"])
    else:
        buckets["mirova_other"] += 1
        mw_without.append((r.get("primary_cluster") or {})["vrp_mw"])

print("Our summit detections classified by what MIROVA reports same instant (±10 min):")
total = sum(buckets.values())
for k, v in buckets.most_common():
    print(f"  {k:<22} {v:>5}  ({100*v/max(total,1):.1f}%)")

print(f"\nOver-detection (no ALERTA/FP MIROVA counterpart): {sum(v for k,v in buckets.items() if k not in ('mirova_ALERTA','mirova_FP'))}/{total}")

# -------- Magnitude comparison --------
print("\nMagnitude comparison (our pc.vrp_mw, MW):")
if mw_with:
    print(f"  with MIROVA ALERTA/FP counterpart (n={len(mw_with)}): median={median(mw_with):.2f}  min={min(mw_with):.2f}  max={max(mw_with):.2f}")
if mw_without:
    print(f"  without ALERTA/FP counterpart   (n={len(mw_without)}): median={median(mw_without):.2f}  min={min(mw_without):.2f}  max={max(mw_without):.2f}")

# For MIROVA ALERTAs, side-by-side magnitude
print("\nSide-by-side magnitude for MIROVA ALERTAs:")
for a in mirova_alerts:
    dt = parse_mirova_dt(a["Fecha_Satelite_UTC"])
    if not dt:
        continue
    candidates = find_ours_near(dt)
    if candidates:
        best_r = max(
            candidates,
            key=lambda r: (r.get("primary_cluster") or {}).get("vrp_mw", 0)
        )
        pc = best_r.get("primary_cluster") or {}
        ours_vrp = pc.get("vrp_mw", 0)
        ours_d = best_r.get("final_hotspot_dist_km")
        try:
            mirova_vrp = float(a["VRP_MW"])
            ratio = ours_vrp / mirova_vrp if mirova_vrp > 0 else float("inf")
        except Exception:
            ratio = float("nan")
        print(f"  {a['Fecha_Satelite_UTC']}  MIROVA={a['VRP_MW']} MW  ours={ours_vrp:.2f} MW  d={ours_d}  ratio={ratio:.2f}x")
    else:
        print(f"  {a['Fecha_Satelite_UTC']}  MIROVA={a['VRP_MW']} MW  ours= (no record)")

# -------- Feature comparison: with vs without MIROVA counterpart --------
def features(records):
    dists = [r["final_hotspot_dist_km"] for r in records if r.get("final_hotspot_dist_km") is not None]
    vrps = [(r.get("primary_cluster") or {}).get("vrp_mw", 0) for r in records]
    npix = [(r.get("primary_cluster") or {}).get("n_pixels", 0) for r in records]
    return {
        "n": len(records),
        "dist_med": median(dists) if dists else None,
        "vrp_med": median(vrps) if vrps else None,
        "npix_med": median(npix) if npix else None,
    }


with_buckets = []
without_buckets = []
for r in our_summit:
    dt = parse_our_dt(r["datetime_utc"])
    if not dt:
        continue
    near = find_mirova_near(dt)
    tipos = [m.get("Tipo_Registro", "?") for m in near] if near else []
    if "ALERTA_TERMICA" in tipos or "FALSO_POSITIVO" in tipos:
        with_buckets.append(r)
    else:
        without_buckets.append(r)

print("\nFeature comparison: summit detections with vs without MIROVA ALERTA/FP counterpart")
fw = features(with_buckets)
fo = features(without_buckets)
print(f"  with    counterpart: n={fw['n']}  dist_med={fw['dist_med']}  pc.vrp_med={fw['vrp_med']}  pc.npix_med={fw['npix_med']}")
print(f"  without counterpart: n={fo['n']}  dist_med={fo['dist_med']}  pc.vrp_med={fo['vrp_med']}  pc.npix_med={fo['npix_med']}")
