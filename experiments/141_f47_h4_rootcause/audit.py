"""F47 H4 root cause audit — NdC vrp_mw rollup vacío.

Pregunta:
  - 121 records tienen primary_cluster.vrp_mw > 0 PERO vrp_mw == 0.
  - Cluster bandera: pc.vrp_mw=332.8 MW @ 0.5 km del vent, clasificado 'far'.
  ¿Por qué?

Hipótesis a verificar empíricamente leyendo el JSON:
  H4a — final_hotspot_dist_km > inner_radius (5 km) aunque pc.centroid_dist_km <= 5
  H4b — eruption-path "robó" final_hotspot a un pixel lejano (~25 km)
  H4c — el zero-out store.py L183-195 (hotspot_dist > 5 km) corre y mata vrp_mw
"""
import json
from collections import Counter
from pathlib import Path

J = Path("data/mirova_equivalent/NevadosDeChillan.json")
INNER = 5.0  # volcanoes.yaml NdC

data = json.loads(J.read_text())
records = data["records"]
total = len(records)

# Filtrar los 121 records de interés
mismatch = []
for r in records:
    pc = (r.get("primary_cluster") or {})
    pc_vrp = pc.get("vrp_mw", 0) or 0
    if pc_vrp > 0 and (r.get("vrp_mw") or 0) == 0:
        mismatch.append(r)

print(f"Total records: {total}")
print(f"Mismatch (pc.vrp_mw>0 & vrp_mw==0): {len(mismatch)}")
print()

# Tabla de campos clave del primer 10
print("=== Primeros 10 records mismatch ===")
hdr = ["dt", "sensor", "dist_class", "fh_dist", "fh_src", "hs_dist", "pc.cdist", "pc.n_pix", "pc.vrp_mw", "discard"]
print("  ".join(f"{h:>12}" for h in hdr))
for r in mismatch[:10]:
    pc = r["primary_cluster"]
    row = [
        (r.get("datetime_utc") or "")[5:16],
        (r.get("sensor") or "")[:10],
        str(r.get("distance_class")),
        f"{r.get('final_hotspot_dist_km')}",
        str(r.get("final_hotspot_source")),
        f"{r.get('hotspot_dist_km')}",
        f"{pc.get('centroid_dist_km')}",
        str(pc.get("n_pixels")),
        f"{pc.get('vrp_mw')}",
        str(r.get("discarded_reason"))[:18],
    ]
    print("  ".join(f"{c:>12}" for c in row))

print()
print("=== Breakdown distance_class de los 121 ===")
print(Counter(r.get("distance_class") for r in mismatch))

print()
print("=== Breakdown final_hotspot_source de los 121 ===")
print(Counter(r.get("final_hotspot_source") for r in mismatch))

print()
print("=== Breakdown discarded_reason de los 121 ===")
print(Counter(r.get("discarded_reason") for r in mismatch))

# ¿En cuántos pc.cdist <= INNER mientras final_hotspot_dist > INNER?
both = 0
inv_only = 0  # pc <= 5 pero final > 5
for r in mismatch:
    pc_d = (r.get("primary_cluster") or {}).get("centroid_dist_km")
    fh_d = r.get("final_hotspot_dist_km")
    if pc_d is not None and pc_d <= INNER:
        if fh_d is not None and fh_d > INNER:
            inv_only += 1
        both += 1

print()
print(f"Mismatch con pc.centroid_dist_km <= {INNER}: {both} / {len(mismatch)}")
print(f"  ... de esos, con final_hotspot_dist_km > {INNER} (inconsistencia summit/far): {inv_only}")

# ¿Y los que tienen hotspot_dist_km (eruption path top pixel) > 5 km?
hs_far = 0
for r in mismatch:
    hs_d = r.get("hotspot_dist_km")
    pc_d = (r.get("primary_cluster") or {}).get("centroid_dist_km", 999)
    if pc_d <= INNER and hs_d is not None and hs_d > INNER:
        hs_far += 1
print(f"Mismatch con pc cerca (<{INNER}) y hotspot_dist_km lejos (>{INNER}): {hs_far}")

# Caso bandera: MODIS_TERRA pc.vrp_mw=332.8 @ 0.5 km
print()
print("=== Caso bandera (pc.vrp_mw entre 330-335, MODIS_TERRA) ===")
for r in records:
    pc = r.get("primary_cluster") or {}
    if pc.get("vrp_mw") and 330 < pc["vrp_mw"] < 335 and "MODIS_TERRA" in (r.get("sensor") or ""):
        print(json.dumps({
            "datetime_utc": r.get("datetime_utc"),
            "sensor": r.get("sensor"),
            "vrp_mw": r.get("vrp_mw"),
            "vrp_vent_mw": r.get("vrp_vent_mw"),
            "n_anomalous_pixels": r.get("n_anomalous_pixels"),
            "triggered_test1": r.get("triggered_test1"),
            "distance_class": r.get("distance_class"),
            "hotspot_lat": r.get("hotspot_lat"),
            "hotspot_lon": r.get("hotspot_lon"),
            "hotspot_dist_km": r.get("hotspot_dist_km"),
            "final_hotspot_lat": r.get("final_hotspot_lat"),
            "final_hotspot_lon": r.get("final_hotspot_lon"),
            "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
            "final_hotspot_source": r.get("final_hotspot_source"),
            "primary_cluster": pc,
            "discarded_reason": r.get("discarded_reason"),
            "discarded_hotspot_dist_km": r.get("discarded_hotspot_dist_km"),
            "discarded_n_pixels": r.get("discarded_n_pixels"),
        }, indent=2))
        break
