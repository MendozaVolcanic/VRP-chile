"""27_crossmatch_vs_consolidado.py — Baseline pre-P3 contra CSV MIROVA NRT.

Compara nuestros JSONs de data/mirova_equivalent/ contra el CSV consolidado
del scraper Mirova-v1 (ground truth operacional S15+). Por cada deteccion
MIROVA (VRP>0 en el CSV) intenta matchear a nuestra pasada correspondiente
dentro de Dt<=15 min y computa TP/FN/FP/ratio_VRP por volcan.

Criterios:
- TP: MIROVA detecta (CSV row VRP>0) Y nosotros detectamos (our vrp_mir_mw>0 o vrp_mw>0).
- FN: MIROVA detecta Y nosotros no (vrp=0 o record ausente).
- FP: nosotros detectamos Y MIROVA no (no hay fila CSV VRP>0 para esa pasada).

Tolerancia MIROVA declarada: VRP +/-30%. Ratio [0.7, 1.3] = "calibrado".

Cobertura conocida: ~100% MODIS, ~80% VIIRS. Cuando MIROVA NO tiene pasada
en el CSV, se asume "gap de observabilidad" y NO se tabula como FP nuestro.

Uso:
  python experiments/27_crossmatch_vs_consolidado.py [--csv X] [--out Y]

Salidas:
  experiments/27_crossmatch_results.json  — detalle por volcan
  stdout                                   — resumen tabla markdown
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


# CSV_sensor -> lista de our-sensor names compatibles
SENSOR_MAP = {
    "MODIS": {"MODIS_TERRA", "MODIS_AQUA"},
    "VIIRS": {"VIIRS_SNPP_750", "VIIRS_NOAA20_750"},   # M-band 750m
    "VIIRS375": {"VIIRS_SNPP", "VIIRS_NOAA20"},        # I-band 375m
}

# CSV volcan name -> yaml name
VOLCANO_MAP = {
    "Lascar": "Lascar",
    "Villarrica": "Villarrica",
    "Chaiten": "Chaiten",
    "Copahue": "Copahue",
    "Isluga": "Isluga",
    "Lastarria": "Lastarria",
    "Llaima": "Llaima",
    "Tupungatito": "Tupungatito",
    "Nevados de Chillan": "NevadosDeChillan",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Peteroa": "PlanchonPeteroa",  # legacy merge
}

DT_MATCH_MIN = 15   # ventana temporal de match


def parse_dt(s: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"bad datetime: {s}")


def load_csv(path: Path):
    """Return (detections_by_vol, all_passes_by_vol).

    detections_by_vol[vol] = list of MIROVA detections (VRP>0).
    all_passes_by_vol[vol] = list of (dt, sensor_csv) for every row in CSV,
        including RUTINA/FALSO_POSITIVO — used to distinguish legit-FP
        ("MIROVA vio, no detecto") from gap ("MIROVA no scrapeo esa pasada").
    """
    det, passes = {}, {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            vol = VOLCANO_MAP.get(r["Volcan"])
            if vol is None:
                continue
            if r["Sensor"] not in SENSOR_MAP:
                continue
            try:
                dt = parse_dt(r["Fecha_Satelite_UTC"])
            except ValueError:
                continue
            passes.setdefault(vol, []).append({
                "dt": dt, "sensor_csv": r["Sensor"],
            })
            try:
                vrp = float(r["VRP_MW"])
                dist = float(r["Distancia_km"])
            except (ValueError, KeyError):
                continue
            if vrp <= 0:
                continue
            det.setdefault(vol, []).append({
                "dt": dt, "sensor_csv": r["Sensor"],
                "vrp_mw": vrp, "dist_km": dist,
            })
    return det, passes


def load_our(volcano_name: str, data_dir: Path) -> list:
    p = data_dir / f"{volcano_name}.json"
    if not p.exists():
        return []
    d = json.load(open(p, "r", encoding="utf-8"))
    recs = d.get("records", [])
    out = []
    for r in recs:
        dt_str = r.get("datetime_utc") or r.get("timestamp_utc")
        if not dt_str:
            continue
        try:
            dt = parse_dt(dt_str)
        except ValueError:
            continue
        vrp = r.get("vrp_mir_mw")
        if vrp is None:
            vrp = r.get("vrp_mw", 0.0) or 0.0
        out.append({
            "dt": dt, "sensor": r.get("sensor", "?"),
            "vrp_mw": float(vrp),
            "final_dist_km": r.get("final_hotspot_dist_km"),
            "distance_class": r.get("distance_class"),
        })
    return out


def find_match(mirova_det: dict, our_recs: list) -> dict | None:
    """Best temporal match within DT_MATCH_MIN, same sensor family."""
    compat = SENSOR_MAP[mirova_det["sensor_csv"]]
    best, best_dt = None, timedelta.max
    for r in our_recs:
        if r["sensor"] not in compat:
            continue
        delta = abs(r["dt"] - mirova_det["dt"])
        if delta < best_dt and delta <= timedelta(minutes=DT_MATCH_MIN):
            best, best_dt = r, delta
    return best


def classify_our(our_rec: dict, detections: list, all_passes: list) -> str:
    """Return one of 'TP-like' (MIROVA detect matches), 'FP' (MIROVA saw but no
    detect), 'GAP' (no MIROVA row for this pasada), 'nodet' (vrp<=0)."""
    if our_rec["vrp_mw"] <= 0:
        return "nodet"
    w = timedelta(minutes=DT_MATCH_MIN)
    # Any MIROVA detection match?
    for d in detections:
        if abs(d["dt"] - our_rec["dt"]) <= w and \
           our_rec["sensor"] in SENSOR_MAP.get(d["sensor_csv"], set()):
            return "TP-like"
    # Any MIROVA pass at all (even RUTINA VRP=0)?
    for p in all_passes:
        if abs(p["dt"] - our_rec["dt"]) <= w and \
           our_rec["sensor"] in SENSOR_MAP.get(p["sensor_csv"], set()):
            return "FP"
    return "GAP"


def crossmatch(detections_by_vol: dict, passes_by_vol: dict, data_dir: Path) -> dict:
    results = {}
    all_vols = set(detections_by_vol) | set(passes_by_vol)
    for vol in all_vols:
        mirova_list = detections_by_vol.get(vol, [])
        passes_list = passes_by_vol.get(vol, [])
        our = load_our(vol, data_dir)
        tp, fn = [], []
        for m in mirova_list:
            match = find_match(m, our)
            if match is None or match["vrp_mw"] <= 0:
                fn.append({"csv": m, "our": match})
            else:
                ratio = match["vrp_mw"] / m["vrp_mw"] if m["vrp_mw"] > 0 else None
                tp.append({"csv": m, "our": match, "ratio": ratio})
        fp, gap = [], []
        for r in our:
            kind = classify_our(r, mirova_list, passes_list)
            if kind == "FP":
                fp.append(r)
            elif kind == "GAP":
                gap.append(r)
        results[vol] = {
            "n_mirova": len(mirova_list),
            "n_our_records": len(our),
            "tp": tp, "fn": fn, "fp": fp, "gap": gap,
        }
    return results


def _median(xs):
    if not xs:
        return None
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def summarize(results: dict):
    print(f"{'Volcan':<22} {'N_CSV':>6} {'TP':>5} {'FN':>5} {'FP':>5} {'GAP':>5} "
          f"{'Recall':>7} {'Prec':>7} {'F1':>6} {'R_med':>7}")
    print("-" * 90)
    totals = {"tp": 0, "fn": 0, "fp": 0, "gap": 0, "ratios": []}
    for vol in sorted(results.keys()):
        r = results[vol]
        tp, fn, fp, gap = len(r["tp"]), len(r["fn"]), len(r["fp"]), len(r["gap"])
        rec = tp / (tp + fn) if (tp + fn) else 0
        prec = tp / (tp + fp) if (tp + fp) else 0
        f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
        ratios = [m["ratio"] for m in r["tp"] if m["ratio"]]
        rm = _median(ratios) or 0
        print(f"{vol:<22} {r['n_mirova']:>6} {tp:>5} {fn:>5} {fp:>5} {gap:>5} "
              f"{rec:>7.2f} {prec:>7.2f} {f1:>6.2f} {rm:>7.2f}")
        totals["tp"] += tp
        totals["fn"] += fn
        totals["fp"] += fp
        totals["gap"] += gap
        totals["ratios"].extend(ratios)
    TP, FN, FP, GAP = totals["tp"], totals["fn"], totals["fp"], totals["gap"]
    rec = TP / (TP + FN) if (TP + FN) else 0
    prec = TP / (TP + FP) if (TP + FP) else 0
    f1 = 2 * rec * prec / (rec + prec) if (rec + prec) else 0
    rm = _median(totals["ratios"]) or 0
    print("-" * 90)
    print(f"{'GLOBAL':<22} {'':<6} {TP:>5} {FN:>5} {FP:>5} {GAP:>5} "
          f"{rec:>7.2f} {prec:>7.2f} {f1:>6.2f} {rm:>7.2f}")
    print()
    print(f"Nota: GAP = nuestras detecciones sin pasada MIROVA en el CSV +/-15min")
    print(f"      (cobertura MIROVA ~100% MODIS, ~80% VIIRS; los GAP no penalizan precision).")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="21_04_2026 registro_vrp_consolidado.csv")
    ap.add_argument("--data-dir", default="data/mirova_equivalent")
    ap.add_argument("--out", default="experiments/27_crossmatch_results.json")
    args = ap.parse_args()

    detections, passes = load_csv(Path(args.csv))
    results = crossmatch(detections, passes, Path(args.data_dir))
    summarize(results)

    # Serialize (datetime -> iso)
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"non-serializable: {type(obj)}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(args.out, "w", encoding="utf-8"),
              indent=2, default=serialize)
    print(f"\nResults saved: {args.out}")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
