"""S94 — Auditoría ESPACIAL (no temporal) VRP Chile vs MIROVA.

Pregunta central: "¿nuestras detecciones caen en el cráter o están dispersas
fuera?" por volcán y por sensor, sobre los 11 Tier A.

READ-ONLY: no toca pipeline/, frontend/, data/ ni .yaml. Solo produce
experiments/_s94_audit/spatial_audit.json (§0.5 integridad: ningún número a
mano, todo deriva del cálculo reproducible aquí).

Convenciones verificadas (A48 — NO inventadas):
- Sensor bucket nuestro:
    MODIS      si 'MODIS' in sensor.upper()
    VIIRS750   si sensor.upper().endswith('_750')
    VIIRS375   si empieza con 'VIIRS' y no termina en _750
- Distancia al cráter (vent): centroid_dist_km / final_hotspot_dist_km YA miden
  desde el vent real (volcanoes.yaml vent_lat/lon), no desde mirova_center.
- Ground truth MIROVA: loader del repo. dist_km de MIROVA se mide desde
  mirova_center (NO desde el cráter) — se reporta aparte, no se mezcla.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json
import statistics
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

TIER_A = [
    "PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue",
    "NevadosDeChillan", "Llaima", "Chaiten", "PlanchonPeteroa",
    "Lastarria", "Isluga", "Tupungatito",
]

# Volcanes con régimen glaciar/lacolito → chequeo de campo difuso.
DIFFUSE_VOLS = {"Tupungatito", "PuyehueCordonCaulle", "NevadosDeChillan"}

CONS_PATH = REPO / "latest_consolidado.csv"
OCR_PATH = REPO / "data" / "mirova_reference" / "registro_vrp_ocr.csv"


def sensor_bucket(sensor: str) -> str:
    s = (sensor or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return "OTHER"


def pctl(vals, q):
    """Percentil simple (interp lineal) sin numpy."""
    if not vals:
        return None
    xs = sorted(vals)
    if len(xs) == 1:
        return xs[0]
    pos = q * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] + (xs[hi] - xs[lo]) * frac


def load_vent_config():
    cfg = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
    out = {}
    for v in cfg["volcanoes"]:
        name = v.get("name")
        if name in TIER_A:
            out[name] = {
                "vent_lat": v.get("vent_lat"),
                "vent_lon": v.get("vent_lon"),
                "inner_radius_km": v.get("inner_radius_km"),
                "mirova_center_lat": v.get("mirova_center_lat"),
                "mirova_center_lon": v.get("mirova_center_lon"),
            }
    return out


def band_of(dist, inner):
    if dist is None:
        return "unknown"
    if dist < 2:
        return "0-2km"
    if dist < 5:
        return "2-5km"
    if dist < inner:
        return "5-inner"
    if dist <= 25:
        return "inner-25km"
    return ">25km"


def analyze_volcano(name, cfg):
    jpath = REPO / "data" / "mirova_equivalent" / f"{name}.json"
    recs = json.load(open(jpath, encoding="utf-8")).get("records", [])
    inner = cfg["inner_radius_km"]

    # Records con detección real: primary_cluster.vrp_mw > 0
    dets = []
    for r in recs:
        pc = r.get("primary_cluster") or {}
        if (pc.get("vrp_mw") or 0) <= 0:
            continue
        dets.append(r)

    out = {
        "inner_radius_km": inner,
        "vent_lat": cfg["vent_lat"],
        "vent_lon": cfg["vent_lon"],
        "n_records_total": len(recs),
        "n_detections_vrp_pos": len(dets),
        "by_sensor": {},
        "all_sensors": None,
    }

    buckets = {"MODIS": [], "VIIRS375": [], "VIIRS750": []}
    for r in dets:
        b = sensor_bucket(r.get("sensor"))
        if b in buckets:
            buckets[b].append(r)
    buckets["ALL"] = dets

    for bname, group in buckets.items():
        if not group:
            stat = {"n": 0}
        else:
            cd = [r["primary_cluster"].get("centroid_dist_km") for r in group]
            cd = [x for x in cd if x is not None]
            dc = [r.get("distance_class") for r in group]
            n_summit = sum(1 for x in dc if x == "summit")
            n_far = sum(1 for x in dc if x == "far")
            bands = {"0-2km": 0, "2-5km": 0, "5-inner": 0,
                     "inner-25km": 0, ">25km": 0, "unknown": 0}
            for x in cd:
                bands[band_of(x, inner)] += 1
            stat = {
                "n": len(group),
                "centroid_dist_km_median": (
                    round(statistics.median(cd), 3) if cd else None),
                "centroid_dist_km_p90": (
                    round(pctl(cd, 0.90), 3) if cd else None),
                "pct_summit": round(100 * n_summit / len(group), 1),
                "pct_far": round(100 * n_far / len(group), 1),
                "n_summit": n_summit,
                "n_far": n_far,
                "bands": bands,
            }
        if bname == "ALL":
            out["all_sensors"] = stat
        else:
            out["by_sensor"][bname] = stat

    # --- Campo difuso (glaciar/lacolito): summit con n_px>=100 y vrp/px<1.0 ---
    if name in DIFFUSE_VOLS:
        n_diffuse = 0
        n_summit_total = 0
        n_summit_lt2km = 0      # summit con cluster <2km del cráter (foco real)
        n_summit_disperse = 0   # summit con cluster >=5km (disperso)
        for r in dets:
            if r.get("distance_class") != "summit":
                continue
            n_summit_total += 1
            pc = r["primary_cluster"]
            npx = pc.get("n_pixels") or 0
            vrp = pc.get("vrp_mw") or 0
            cd = pc.get("centroid_dist_km")
            vrp_per_px = (vrp / npx) if npx else None
            if npx >= 100 and vrp_per_px is not None and vrp_per_px < 1.0:
                n_diffuse += 1
            if cd is not None and cd < 2:
                n_summit_lt2km += 1
            if cd is not None and cd >= 5:
                n_summit_disperse += 1
        out["diffuse_field_check"] = {
            "n_summit_total": n_summit_total,
            "n_summit_diffuse_signature": n_diffuse,  # npx>=100 & vrp/px<1.0
            "n_summit_lt2km": n_summit_lt2km,
            "n_summit_ge5km": n_summit_disperse,
        }

    return out


def analyze_mirova(name, cfg):
    al = load_mirova_alertas(cons_path=str(CONS_PATH), ocr_path=str(OCR_PATH),
                             volcano=name)
    by = {"MODIS": [], "VIIRS375": [], "VIIRS750": [], "ALL": []}
    for a in al:
        d = a.get("dist_km")
        if d is None:
            continue
        by["ALL"].append(d)
        b = a.get("sensor_bucket")
        if b in by:
            by[b].append(d)
    out = {"_note": "dist_km MIROVA medida desde mirova_center, NO desde el crater"}
    for k, v in by.items():
        out[k] = {
            "n_with_dist": len(v),
            "dist_km_median": round(statistics.median(v), 3) if v else None,
            "dist_km_p90": round(pctl(v, 0.90), 3) if v else None,
        }
    out["n_alertas_total"] = len(al)
    return out


def main():
    cfg_all = load_vent_config()
    result = {
        "_meta": {
            "question": "espacial: cae en el crater o disperso fuera?",
            "dist_ours_from": "vent real (volcanoes.yaml vent_lat/lon)",
            "dist_mirova_from": "mirova_center (offset hasta ~5km del crater)",
            "detection_filter": "primary_cluster.vrp_mw > 0",
            "sensor_bucket": "MODIS / VIIRS750(_750) / VIIRS375(VIIRS sin _750)",
        },
        "volcanoes": {},
    }
    for name in TIER_A:
        cfg = cfg_all.get(name)
        if cfg is None:
            result["volcanoes"][name] = {"error": "no en volcanoes.yaml Tier A"}
            continue
        result["volcanoes"][name] = {
            "ours": analyze_volcano(name, cfg),
            "mirova": analyze_mirova(name, cfg),
        }

    outpath = Path(__file__).resolve().parent / "spatial_audit.json"
    json.dump(result, open(outpath, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"OK -> {outpath}")

    # --- Resumen compacto a stdout (derivado, no a mano) ---
    print("\n=== RESUMEN POR VOLCAN (ALL sensors) ===")
    print(f"{'vol':<22}{'inner':>6}{'n_det':>7}{'med_km':>8}"
          f"{'p90_km':>8}{'%summit':>8}{'%far':>7}")
    for name in TIER_A:
        v = result["volcanoes"][name]
        if "error" in v:
            continue
        a = v["ours"]["all_sensors"]
        inner = v["ours"]["inner_radius_km"]
        if a.get("n", 0) == 0:
            print(f"{name:<22}{inner:>6}{0:>7}")
            continue
        print(f"{name:<22}{inner:>6}{a['n']:>7}"
              f"{a['centroid_dist_km_median']:>8}"
              f"{a['centroid_dist_km_p90']:>8}"
              f"{a['pct_summit']:>8}{a['pct_far']:>7}")

    print("\n=== POR SENSOR: mediana centroid_dist_km (n) ===")
    print(f"{'vol':<22}{'MODIS':>16}{'VIIRS375':>16}{'VIIRS750':>16}")
    for name in TIER_A:
        v = result["volcanoes"][name]
        if "error" in v:
            continue
        bs = v["ours"]["by_sensor"]

        def cell(b):
            s = bs.get(b, {})
            if s.get("n", 0) == 0:
                return "-"
            return f"{s['centroid_dist_km_median']}({s['n']})"
        print(f"{name:<22}{cell('MODIS'):>16}"
              f"{cell('VIIRS375'):>16}{cell('VIIRS750'):>16}")

    print("\n=== CAMPO DIFUSO (glaciar/lacolito) ===")
    for name in TIER_A:
        v = result["volcanoes"][name]
        if "error" in v:
            continue
        df = v["ours"].get("diffuse_field_check")
        if df:
            print(f"{name}: summit={df['n_summit_total']} "
                  f"difuso(npx>=100&vrp/px<1)={df['n_summit_diffuse_signature']} "
                  f"<2km={df['n_summit_lt2km']} >=5km={df['n_summit_ge5km']}")

    print("\n=== MIROVA dist mediana (desde mirova_center) ALL ===")
    for name in TIER_A:
        v = result["volcanoes"][name]
        if "error" in v:
            continue
        m = v["mirova"]["ALL"]
        print(f"{name:<22} n={m['n_with_dist']:<5} "
              f"med={m['dist_km_median']} p90={m['dist_km_p90']} "
              f"(total alertas={v['mirova']['n_alertas_total']})")


if __name__ == "__main__":
    main()
