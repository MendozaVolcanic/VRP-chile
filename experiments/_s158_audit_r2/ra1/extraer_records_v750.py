# -*- coding: utf-8 -*-
"""RA1: extrae de data/mirova_equivalent/*.json los records VIIRS 750 con cumulo (primary_cluster) a un JSON plano
para que (a) el predicado del tablero corra con node sobre ellos y (b) el cruce con MIROVA los lea.

Convencion de sensor comprobada con Counter en esta sesion (A48): sufijo _750 = M-band.
inner_radius_km por volcan: volcanoes.yaml (solo lectura).
"""
from __future__ import annotations

import glob
import json
import os
from collections import Counter

import yaml

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records_v750.json")


def main():
    vols = yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))
    vols = vols.get("volcanoes", vols) if isinstance(vols, dict) else vols
    inner = {}
    for v in vols:
        inner[v["name"]] = v.get("inner_radius_km")
    out = []
    c_sensor = Counter()
    n_total = n_750 = 0
    for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
        vol = os.path.basename(f)[:-5]
        d = json.load(open(f, encoding="utf-8"))
        recs = d if isinstance(d, list) else d.get("records")
        for r in recs:
            n_total += 1
            s = r.get("sensor", "")
            c_sensor[s] += 1
            if not s.endswith("_750"):
                continue
            n_750 += 1
            pc = r.get("primary_cluster")
            if not pc:
                continue
            ap = r.get("anomaly_pixels") or []
            out.append({
                "volcano": vol,
                "inner_radius_km": inner.get(vol),
                "sensor": s,
                "datetime_utc": r.get("datetime_utc"),
                "distance_class": r.get("distance_class"),
                "vrp_mw": r.get("vrp_mw"),
                "vrp_mir_mw": r.get("vrp_mir_mw"),
                "triggered_test1": r.get("triggered_test1"),
                "discarded_reason": r.get("discarded_reason"),
                "primary_cluster": pc,
                "final_hotspot_source": r.get("final_hotspot_source"),
                "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
                "t_bg_k": r.get("t_bg_k"),
                "t_max_k": r.get("t_max_k"),
                "diag_L_bg": r.get("diag_L_bg_w_m2_sr_um"),
                "n_anomalous_pixels": r.get("n_anomalous_pixels"),
                "n_pixels_json": len(ap),
                "ap_bt_max": max((p.get("bt_k") or 0) for p in ap) if ap else None,
                "ap_bt_min": min((p.get("bt_k") or 9e9) for p in ap) if ap else None,
                "ap_vrp_sum": sum((p.get("vrp_mw") or 0) for p in ap) if ap else None,
                "diag_sanity_cap": r.get("diag_sanity_cap_threshold_mw"),
                "diag_vrp_raw_mw": r.get("diag_vrp_raw_mw"),
                "regimen_sha": (r.get("regimen") or {}).get("codigo_sha"),
                "sensor_zenith_deg": r.get("sensor_zenith_deg"),
                "diag_n_bg_anillo": r.get("diag_n_bg_anillo"),
                "diag_sigma_bg_k": r.get("diag_sigma_bg_k"),
            })
    json.dump(out, open(OUT, "w", encoding="utf-8"))
    print("records totales en data/mirova_equivalent: %d ; VIIRS 750: %d ; con primary_cluster: %d" % (n_total, n_750, len(out)))
    print("Counter sensores:", dict(c_sensor))
    print("escrito", OUT)


if __name__ == "__main__":
    main()
