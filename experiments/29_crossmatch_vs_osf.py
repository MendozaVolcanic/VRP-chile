"""29_crossmatch_vs_osf.py — Crossmatch nuestros JSONs vs OSF v2.5 (25 anos).

Complemento de 27_crossmatch_vs_consolidado.py. Mientras ese compara contra
el CSV NRT 3.5 meses (poder estadistico limitado), este compara contra OSF
v2.5 archive (615k filas, 2000-2025, ~50x mas masa para Lascar y Lastarria).

Util para validar P3.2 sobre ventana historica: si nuestro pipeline
reprocesa Lascar 2013 (pico 2012 activo), deberia matchear OSF records de
ese ano. Si P3.2 regresiono, se nota aqui.

Nota: OSF incompleto para VIIRS_M (ratio 4-9x vs NRT). Usar solo MODIS y
VIIRS_I para crossmatch; reportar VIIRS_M por completitud pero no critico.

Uso:
  python experiments/29_crossmatch_vs_osf.py \
    [--year 2013] [--volcano Lascar] [--data-dir data/mirova_equivalent]

Salida:
  experiments/29_crossmatch_vs_osf_results.json
  stdout tabla per-volcan
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


VOLCANO_MAP_OSF_TO_YAML = {
    "Láscar": "Lascar",
    "Chaitén": "Chaiten",
    "Villarrica": "Villarrica",
    "Copahue": "Copahue",
    "Isluga": "Isluga",
    "Lastarria": "Lastarria",
    "Llaima": "Llaima",
    "Chillán, Nevados de": "NevadosDeChillan",
    "Planchón-Peteroa": "PlanchonPeteroa",
    "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
}

# Resolution -> our sensor family
RES_TO_OURS = {
    1000: {"MODIS_TERRA", "MODIS_AQUA"},
    750:  {"VIIRS_SNPP_750", "VIIRS_NOAA20_750"},
    375:  {"VIIRS_SNPP", "VIIRS_NOAA20"},
}


def parse_osf_time(s: str):
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_osf(path: Path, year: int = None, volcano_filter: str = None):
    det = {}
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            osf_name = r.get("Volc_Name", "")
            if osf_name not in VOLCANO_MAP_OSF_TO_YAML:
                continue
            vol = VOLCANO_MAP_OSF_TO_YAML[osf_name]
            if volcano_filter and vol != volcano_filter:
                continue
            try:
                vrp_mw = float(r["VRP"]) / 1e6   # OSF stores in Watts
                res = int(r["Resolution"])
                dt = parse_osf_time(r["timeUTC"])
            except (ValueError, KeyError, TypeError):
                continue
            if dt is None or vrp_mw <= 0:
                continue
            if year is not None and dt.year != year:
                continue
            if res not in RES_TO_OURS:
                continue
            det.setdefault(vol, []).append({
                "dt": dt, "vrp_mw": vrp_mw, "res": res,
                "max_dist_km": float(r.get("Max_Dist") or 0) / 1000.0,
            })
    return det


def load_our(volcano: str, data_dir: Path):
    p = data_dir / f"{volcano}.json"
    if not p.exists():
        return []
    d = json.load(open(p, "r", encoding="utf-8"))
    out = []
    for r in d.get("records", []):
        dt_str = r.get("datetime_utc")
        if not dt_str:
            continue
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        vrp = r.get("vrp_mir_mw") or r.get("vrp_mw") or 0.0
        out.append({
            "dt": dt, "sensor": r.get("sensor", "?"),
            "vrp_mw": float(vrp),
        })
    return out


def match(osf_det: dict, ours: list, dt_window_min: int = 15):
    compat = RES_TO_OURS[osf_det["res"]]
    best, best_dt = None, timedelta.max
    for r in ours:
        if r["sensor"] not in compat:
            continue
        delta = abs(r["dt"] - osf_det["dt"])
        if delta < best_dt and delta <= timedelta(minutes=dt_window_min):
            best, best_dt = r, delta
    return best


def run(osf_by_vol: dict, data_dir: Path):
    results = {}
    for vol, osf_list in osf_by_vol.items():
        ours = load_our(vol, data_dir)
        tp, fn = [], []
        for m in osf_list:
            om = match(m, ours)
            if om is None or om["vrp_mw"] <= 0:
                fn.append(m)
            else:
                ratio = om["vrp_mw"] / m["vrp_mw"] if m["vrp_mw"] > 0 else None
                tp.append({"osf": m, "our": om, "ratio": ratio})
        results[vol] = {"n_osf": len(osf_list), "tp": tp, "fn": fn,
                        "n_our": len(ours)}
    return results


def summarize(results: dict):
    print(f"{'Volcan':<22} {'N_OSF':>6} {'TP':>5} {'FN':>5} "
          f"{'Recall':>7} {'R_med':>7}")
    print("-" * 57)
    for vol in sorted(results.keys()):
        r = results[vol]
        tp = len(r["tp"]); fn = len(r["fn"])
        rec = tp / (tp + fn) if (tp + fn) else 0
        ratios = [m["ratio"] for m in r["tp"] if m.get("ratio")]
        rm = median(ratios) if ratios else 0
        print(f"{vol:<22} {r['n_osf']:>6} {tp:>5} {fn:>5} "
              f"{rec:>7.2f} {rm:>7.2f}")


def _json_ready(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"non-serializable: {type(obj)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--osf", default="data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv")
    ap.add_argument("--data-dir", default="data/mirova_equivalent")
    ap.add_argument("--year", type=int, default=None,
                    help="Filtrar OSF a un ano (ej: 2013). Default: todos.")
    ap.add_argument("--volcano", default=None,
                    help="Filtrar un volcan. Default: todos.")
    ap.add_argument("--out", default="experiments/29_crossmatch_vs_osf_results.json")
    args = ap.parse_args()

    print(f"Cargando OSF desde {args.osf}...")
    det = load_osf(Path(args.osf), year=args.year, volcano_filter=args.volcano)
    total = sum(len(v) for v in det.values())
    print(f"  {total} detecciones OSF filtradas "
          f"(year={args.year}, volcano={args.volcano}).")
    print()

    results = run(det, Path(args.data_dir))
    summarize(results)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(results, open(args.out, "w", encoding="utf-8"),
              indent=2, default=_json_ready)
    print(f"\nGuardado: {args.out}")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
