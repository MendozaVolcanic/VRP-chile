"""S51-AUDIT-VILLARRICA: exhaustive audit across all profiles + tags.

For every profile dir containing Villarrica.json, report:
- total records
- summit (<5 km) count
- far count
- first/last record date
- any 'anomaly_pixels' fields with pixel count
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

INNER_KM = 5.0  # Villarrica inner_radius_km in volcanoes.yaml

rows = []
for sub in sorted(DATA.iterdir()):
    if not sub.is_dir():
        continue
    f = sub / "Villarrica.json"
    if not f.exists():
        continue
    try:
        payload = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        rows.append((sub.name, "ERR", str(e), "", "", "", ""))
        continue
    if isinstance(payload, dict):
        records = payload.get("records", [])
    elif isinstance(payload, list):
        records = payload
    else:
        rows.append((sub.name, "BADTYPE", "", "", "", "", ""))
        continue
    total = len(records)
    summit = 0
    far = 0
    n_anom_pix_records = 0
    max_anom_pix = 0
    first_dt = None
    last_dt = None
    for r in records:
        dt = r.get("datetime") or r.get("timestamp") or ""
        if dt:
            if first_dt is None or dt < first_dt:
                first_dt = dt
            if last_dt is None or dt > last_dt:
                last_dt = dt
        # distance: prefer final_hotspot_dist_km, fall back to hotspot_dist_km
        d = r.get("final_hotspot_dist_km")
        if d is None:
            d = r.get("hotspot_dist_km")
        if d is None:
            # try pc.dist
            pc = r.get("primary_cluster") or {}
            d = pc.get("dist_km")
        if d is not None:
            if d <= INNER_KM:
                summit += 1
            else:
                far += 1
        ap = r.get("anomaly_pixels")
        if ap:
            n_anom_pix_records += 1
            if isinstance(ap, list):
                max_anom_pix = max(max_anom_pix, len(ap))
    rows.append((
        sub.name, str(total), str(summit), str(far),
        first_dt or "", last_dt or "",
        f"{n_anom_pix_records}/{max_anom_pix}",
    ))

# Print sorted by summit count desc
rows_sorted = sorted(rows, key=lambda r: int(r[2]) if r[2].isdigit() else -1, reverse=True)
print(f"{'profile':<40} {'total':>6} {'summit':>6} {'far':>4} {'first':<25} {'last':<25} {'anom_pix(N/max)':<15}")
print("-" * 130)
for r in rows_sorted:
    print(f"{r[0]:<40} {r[1]:>6} {r[2]:>6} {r[3]:>4} {r[4]:<25} {r[5]:<25} {r[6]:<15}")
