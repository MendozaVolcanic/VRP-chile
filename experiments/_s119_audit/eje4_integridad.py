# -*- coding: utf-8 -*-
"""Eje 4.1 auditoria S119 — integridad de los 45 JSONs data/mirova_equivalent/.

Chequeos:
  (a) errores de parseo JSON (corrupcion A47-style)
  (b) duplicados por (datetime_utc, sensor) por volcan
  (c) mezcla product_version nrt/standard por volcan (%)
  (d) primary_cluster null pero vrp_mw > 0 (posible incoherencia; puede ser
      legitimo scene-wide sin cluster — se cuentan y se listan ejemplos)
  (e) distance_class == 'summit' con primary_cluster.centroid_dist... — usamos
      distancia haversine centroid vs (vent si existe, sino lat/lon volcan)
      > inner_radius_km y final_hotspot_source != 'cluster_rescue'

Output: experiments/_s119_audit/eje4_integridad.json
Criterio pass: 0 en (a) y (b).
"""
import sys, io, json, math
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "mirova_equivalent"
OUT = Path(__file__).resolve().parent / "eje4_integridad.json"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_volcano_config():
    cfg = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
    out = {}
    for v in cfg["volcanoes"]:
        out[v["name"]] = {
            "inner_radius_km": v.get("inner_radius_km"),
            "lat": v.get("lat"),
            "lon": v.get("lon"),
            "vent_lat": v.get("vent_lat"),
            "vent_lon": v.get("vent_lon"),
        }
    return out


def main():
    vcfg = load_volcano_config()
    files = sorted(DATA.glob("*.json"))  # excluye .cleanbackup etc (no matchean *.json)
    report = {
        "n_files": len(files),
        "a_parse_errors": [],
        "b_duplicates": {},          # vol -> n pares duplicados (records extra)
        "b_duplicates_total": 0,
        "c_product_version": {},     # vol -> {standard, nrt, otros, pct_nrt}
        "d_pc_null_vrp_pos": {},     # vol -> count
        "d_examples": [],
        "e_summit_outside_inner": {},
        "e_examples": [],
        "verdict": None,
    }

    for f in files:
        vol = f.stem
        try:
            doc = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            report["a_parse_errors"].append({"file": f.name, "error": str(e)})
            continue
        recs = doc.get("records", []) if isinstance(doc, dict) else doc

        # (b) duplicados
        keys = Counter((r.get("datetime_utc"), r.get("sensor")) for r in recs)
        dups = {k: c for k, c in keys.items() if c > 1}
        if dups:
            extra = sum(c - 1 for c in dups.values())
            report["b_duplicates"][vol] = {
                "n_claves_duplicadas": len(dups),
                "n_records_extra": extra,
                "ejemplos": [list(k) + [c] for k, c in list(dups.items())[:3]],
            }
            report["b_duplicates_total"] += extra

        # (c) product_version
        pv = Counter(r.get("product_version") for r in recs)
        tot = sum(pv.values())
        report["c_product_version"][vol] = {
            "total": tot,
            "standard": pv.get("standard", 0),
            "nrt": pv.get("nrt", 0),
            "otros": tot - pv.get("standard", 0) - pv.get("nrt", 0),
            "pct_nrt": round(100.0 * pv.get("nrt", 0) / tot, 1) if tot else None,
        }

        # (d) primary_cluster null + vrp_mw > 0
        d_hits = [r for r in recs
                  if r.get("primary_cluster") is None and (r.get("vrp_mw") or 0) > 0]
        if d_hits:
            report["d_pc_null_vrp_pos"][vol] = len(d_hits)
            for r in d_hits[:2]:
                report["d_examples"].append({
                    "vol": vol, "datetime_utc": r.get("datetime_utc"),
                    "sensor": r.get("sensor"), "vrp_mw": r.get("vrp_mw"),
                    "n_anomalous_pixels": r.get("n_anomalous_pixels"),
                    "distance_class": r.get("distance_class"),
                    "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
                    "final_hotspot_source": r.get("final_hotspot_source"),
                })

        # (e) summit con centroide fuera del inner_radius sin cluster_rescue
        cfg = vcfg.get(vol)
        if cfg and cfg["inner_radius_km"]:
            ref_lat = cfg["vent_lat"] if cfg["vent_lat"] is not None else cfg["lat"]
            ref_lon = cfg["vent_lon"] if cfg["vent_lon"] is not None else cfg["lon"]
            inner = cfg["inner_radius_km"]
            e_hits = []
            for r in recs:
                if r.get("distance_class") != "summit":
                    continue
                pc = r.get("primary_cluster")
                if not pc or pc.get("centroid_lat") is None:
                    continue
                if r.get("final_hotspot_source") == "cluster_rescue":
                    continue
                d = haversine_km(ref_lat, ref_lon, pc["centroid_lat"], pc["centroid_lon"])
                if d > inner:
                    e_hits.append((r, d))
            if e_hits:
                report["e_summit_outside_inner"][vol] = {
                    "count": len(e_hits), "inner_radius_km": inner,
                }
                for r, d in e_hits[:2]:
                    report["e_examples"].append({
                        "vol": vol, "datetime_utc": r.get("datetime_utc"),
                        "sensor": r.get("sensor"),
                        "centroid_dist_km_calc": round(d, 2),
                        "pc_centroid_dist_km_field": r.get("primary_cluster", {}).get("centroid_dist_km"),
                        "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
                        "final_hotspot_source": r.get("final_hotspot_source"),
                        "pc_vrp_mw": r.get("primary_cluster", {}).get("vrp_mw"),
                    })

    n_a = len(report["a_parse_errors"])
    n_b = report["b_duplicates_total"]
    report["verdict"] = {
        "a_parse_errors": n_a,
        "b_duplicate_records_extra": n_b,
        "c_vols_con_mezcla_nrt": sum(1 for v in report["c_product_version"].values()
                                     if v["nrt"] > 0 and v["standard"] > 0),
        "d_total": sum(report["d_pc_null_vrp_pos"].values()),
        "e_total": sum(v["count"] for v in report["e_summit_outside_inner"].values()),
        "pass_a_b": (n_a == 0 and n_b == 0),
    }

    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(report["verdict"], indent=2, ensure_ascii=False))
    print("b_duplicates vols:", {k: v["n_records_extra"] for k, v in report["b_duplicates"].items()})
    print("d por vol:", report["d_pc_null_vrp_pos"])
    print("e por vol:", {k: v["count"] for k, v in report["e_summit_outside_inner"].items()})
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
