"""S88 Frente A — validación post-reproceso (correr DESPUÉS del workflow).

Compara el match 1:1 anomalía dominante de Lascar feb entre:
  - el operacional persistido (data/mirova_equivalent/Lascar.json, primary stale)
  - el reproceso con config actual (data/_s88_reproc_validation/Lascar.json)

Hipótesis S88: los 8 detection-loss + 2 borde de febrero, que en el operacional
tienen el primary a 18-31 km (cráter ausente del top-N), en el reproceso deberían
apuntar al cráter (<2 km de mirova_center) porque el pipeline actual (bt_path OFF
S40 + gates intra-radio S84/S85 + vent_anchored) no llena el top-100 con pixeles
del Salar. Si se confirma, valida que el gap de Lascar es deuda histórica, no bug
actual.

Uso: python experiments/_s88_lascar_reselect/post_reproc_validate.py
(requiere que el workflow reproc-s88-lascar-validation.yml haya corrido y
commiteado data/_s88_reproc_validation/Lascar.json).
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

CHILE_TZ = "America/Santiago"
CONS = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"
OCR = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
OLD = ROOT / "data/mirova_equivalent/Lascar.json"
NEW = ROOT / "data/_s88_reproc_validation/Lascar.json"
TOL = 2.0


def hav(a, b, c, d):
    R = 6371.0
    p = math.radians
    dlat, dlon = p(c - a), p(d - b)
    x = math.sin(dlat / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


VY = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
LAS = next(v for v in VY["volcanoes"] if v["name"] == "Lascar")
MC = (float(LAS["mirova_center_lat"]), float(LAS["mirova_center_lon"]))


def sb(s):
    s = (s or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def primary_dist(r):
    pc = r.get("primary_cluster") or {}
    if pc.get("centroid_lat") is None:
        return None
    return hav(MC[0], MC[1], float(pc["centroid_lat"]), float(pc["centroid_lon"]))


def dominant_by_night(path):
    """{(sensor_bucket, night): primary_dist del record mayor VRP de escena}"""
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    best = {}
    for r in data.get("records", []):
        if not r.get("anomaly_pixels"):
            continue
        b = sb(r.get("sensor", ""))
        if b is None:
            continue
        dt = pd.to_datetime(r.get("datetime_utc"), utc=True, errors="coerce")
        if pd.isna(dt) or dt.year != 2026 or dt.month != 2:
            continue
        night = dt.tz_convert(CHILE_TZ).date()
        scene_vrp = sum(p.get("vrp_mw", 0) for p in r["anomaly_pixels"])
        key = (b, str(night))
        if key not in best or scene_vrp > best[key][1]:
            best[key] = (primary_dist(r), scene_vrp)
    return {k: v[0] for k, v in best.items()}


# MIROVA dominante feb
mir = pd.DataFrame(load_mirova_alertas(str(CONS), str(OCR)))
mir = mir[mir["volcano"] == "Lascar"].copy()
mir["dt"] = pd.to_datetime(mir["fecha_utc"], utc=True, errors="coerce")
mir = mir[mir["dt"].notna()]
mir = mir[(mir["dt"].dt.year == 2026) & (mir["dt"].dt.month == 2)]
mir["night"] = mir["dt"].dt.tz_convert(CHILE_TZ).dt.date
mir_dom = {}
for (b, n), g in mir.groupby(["sensor_bucket", "night"]):
    best = g.loc[g["vrp_mw"].idxmax()]
    if pd.notna(best["dist_km"]):
        mir_dom[(b, str(n))] = float(best["dist_km"])

old = dominant_by_night(OLD)
new = dominant_by_night(NEW)

if new is None:
    print("[PENDIENTE] data/_s88_reproc_validation/Lascar.json no existe todavía.")
    print("Corré primero el workflow reproc-s88-lascar-validation.yml y hacé git pull.")
    sys.exit(0)


def ok(our, mir_d):
    return our is not None and mir_d is not None and abs(our - mir_d) <= TOL


rows = []
old_m = new_m = n = 0
for key in sorted(mir_dom):
    md = mir_dom[key]
    od, nd = old.get(key), new.get(key)
    n += 1
    o_ok, n_ok = ok(od, md), ok(nd, md)
    old_m += o_ok
    new_m += n_ok
    flip = "FLIP→OK" if (n_ok and not o_ok) else ("regресión" if (o_ok and not n_ok) else "")
    rows.append((key[1], key[0], round(md, 2),
                 round(od, 2) if od is not None else None,
                 round(nd, 2) if nd is not None else None, o_ok, n_ok, flip))

print("=== VALIDACIÓN POST-REPROCESO LASCAR FEB (tol 2km) ===")
print(f"{'night':<12}{'sens':<10}{'mir':>6}{'old':>7}{'new':>7}{'oOK':>5}{'nOK':>5}  nota")
for r in rows:
    print(f"{r[0]:<12}{r[1]:<10}{r[2]:>6}{str(r[3]):>7}{str(r[4]):>7}{str(r[5]):>5}{str(r[6]):>5}  {r[7]}")
print(f"\nMatch old (operacional stale): {old_m}/{n} = {100*old_m/n:.1f}%")
print(f"Match new (config actual reproc): {new_m}/{n} = {100*new_m/n:.1f}%")
print(f"Delta: {new_m-old_m:+d} records ({100*(new_m-old_m)/n:+.1f}pp)")
