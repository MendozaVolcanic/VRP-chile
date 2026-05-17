"""S47 — D9 residual check post-drift234 adoption.

Para los 4 FN Lascar MODIS canónicos (S45) y para todos los Tier A:
1) Lascar 4 casos: ¿son TP, FP o FN post-drift234?
2) Para 11 Tier A, % records con primary_cluster summit (centroid_dist <= inner_radius) vs lejano.
3) Buscar casos análogos donde anomaly_pixels contiene un pixel summit
   pero primary_cluster.centroid_dist > 2 * inner_radius (D9 residual).
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "mirova_equivalent"
VOLC_YAML = ROOT / "volcanoes.yaml"

# Tier A operacionales
TIER_A = [
    "Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
    "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
    "Tupungatito", "Villarrica",
]

# inner_radius_km por volcán (de CLAUDE.md tabla S14)
INNER = {
    "Chaiten": 5, "Copahue": 4, "Isluga": 5, "Lascar": 5, "Lastarria": 3,
    "Llaima": 5, "NevadosDeChillan": 5, "PlanchonPeteroa": 3,
    "PuyehueCordonCaulle": 20, "Tupungatito": 7, "Villarrica": 5,
}

# Los 4 FN Lascar MODIS canónicos S45 (UTC strings prefix)
LASCAR_CANONICAL = [
    "2026-04-30T07:30", "2026-04-28T07:50",
    "2026-04-28T01:50", "2026-04-27T07:15",
]


def load(vol: str) -> list[dict]:
    p = DATA / f"{vol}.json"
    if not p.exists():
        return []
    obj = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(obj, dict):
        return obj.get("records", []) or []
    return obj


def centroid_dist(rec: dict) -> float | None:
    pc = rec.get("primary_cluster") or {}
    d = pc.get("centroid_dist_km")
    if d is None:
        d = rec.get("final_hotspot_dist_km")
    return d


def has_summit_pixel(rec: dict, inner: float) -> bool:
    ap = rec.get("anomaly_pixels") or []
    for px in ap:
        d = px.get("dist_km")
        if d is not None and d <= inner:
            return True
    return False


def n_anom(rec: dict) -> int:
    v = rec.get("n_anomalous_pixels")
    if v is not None:
        return v
    return len(rec.get("anomaly_pixels") or [])


# ===== 1) Lascar 4 FN canónicos =====
print("=" * 70)
print("1) LASCAR 4 FN CANONICAL S45 — estado post-drift234")
print("=" * 70)
lascar = load("Lascar")
inner_l = INNER["Lascar"]
print(f"Total Lascar records: {len(lascar)}")
matches = []
for prefix in LASCAR_CANONICAL:
    found = [r for r in lascar if str(r.get("datetime", "")).startswith(prefix)
             or str(r.get("timestamp", "")).startswith(prefix)
             or str(r.get("ts", "")).startswith(prefix)]
    matches.append((prefix, found))

for prefix, found in matches:
    if not found:
        print(f"  {prefix}: NO RECORD (no procesado o ventana)")
        continue
    for rec in found:
        sensor = rec.get("sensor") or rec.get("product") or "?"
        cd = centroid_dist(rec)
        vrp = (rec.get("primary_cluster") or {}).get("vrp_mw")
        if vrp is None:
            vrp = rec.get("vrp_mw")
        n = n_anom(rec)
        summit_px = has_summit_pixel(rec, inner_l)
        cls = rec.get("distance_class") or "?"
        ts = rec.get("datetime") or rec.get("timestamp") or rec.get("ts")
        print(f"  {prefix} ({ts}) {sensor}: pc.dist={cd}km vrp={vrp} "
              f"n_anom={n} summit_px={summit_px} class={cls}")


# ===== 2) Distribución summit vs far primary_cluster (11 Tier A) =====
print()
print("=" * 70)
print("2) DISTRIBUCION primary_cluster summit vs far — 11 Tier A")
print("=" * 70)
print(f"{'Volcan':<22} {'N_rec':>6} {'summit':>7} {'%sum':>6} {'far':>6} "
      f"{'%far':>6} {'no_dist':>7}")
totals = defaultdict(int)
for vol in TIER_A:
    recs = load(vol)
    inner = INNER[vol]
    n_tot = len(recs)
    n_summit = n_far = n_nodist = 0
    for r in recs:
        if n_anom(r) == 0:
            continue
        d = centroid_dist(r)
        if d is None:
            n_nodist += 1
            continue
        if d <= inner:
            n_summit += 1
        else:
            n_far += 1
    n_with = n_summit + n_far + n_nodist
    pct_sum = (100.0 * n_summit / n_with) if n_with else 0
    pct_far = (100.0 * n_far / n_with) if n_with else 0
    print(f"{vol:<22} {n_with:>6} {n_summit:>7} {pct_sum:>5.1f}% "
          f"{n_far:>6} {pct_far:>5.1f}% {n_nodist:>7}")
    totals["summit"] += n_summit
    totals["far"] += n_far
    totals["nodist"] += n_nodist
tot_with = totals["summit"] + totals["far"] + totals["nodist"]
if tot_with:
    print(f"{'TOTAL':<22} {tot_with:>6} {totals['summit']:>7} "
          f"{100.0*totals['summit']/tot_with:>5.1f}% {totals['far']:>6} "
          f"{100.0*totals['far']/tot_with:>5.1f}% {totals['nodist']:>7}")


# ===== 3) D9 residual: summit pixel presente pero primary_cluster lejano =====
print()
print("=" * 70)
print("3) D9 RESIDUAL — summit pixel EN anomaly_pixels pero pc.centroid > 2*inner")
print("=" * 70)
residuals = []
for vol in TIER_A:
    inner = INNER[vol]
    for r in load(vol):
        if n_anom(r) == 0:
            continue
        d = centroid_dist(r)
        if d is None or d <= 2 * inner:
            continue
        # primary_cluster muy lejos → ver si hay pixel summit ignorado
        if has_summit_pixel(r, inner):
            ts = r.get("datetime") or r.get("timestamp") or r.get("ts")
            sensor = r.get("sensor") or r.get("product") or "?"
            pc = r.get("primary_cluster") or {}
            residuals.append({
                "vol": vol, "ts": ts, "sensor": sensor,
                "pc_dist": d, "pc_vrp": pc.get("vrp_mw"),
                "n_anom": n_anom(r), "inner": inner,
            })
print(f"Total D9 residual candidates: {len(residuals)}")
for r in residuals[:30]:
    print(f"  {r['vol']:<22} {r['ts']} {r['sensor']:<14} "
          f"pc_dist={r['pc_dist']:.1f}km inner={r['inner']} "
          f"pc_vrp={r['pc_vrp']} n_anom={r['n_anom']}")

# Save full residuals list
out = ROOT / "experiments" / "89_d9_residual_check.json"
out.write_text(json.dumps({
    "lascar_canonical": [
        {"prefix": p, "n_found": len(f)} for p, f in matches
    ],
    "tier_a_summary": dict(totals),
    "n_residuals": len(residuals),
    "residuals": residuals,
}, indent=2, default=str), encoding="utf-8")
print(f"\nSaved: {out}")
