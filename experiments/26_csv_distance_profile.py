"""26_csv_distance_profile.py — Perfil de distancias MIROVA por volcán.

Lee el CSV consolidado del scraper Mirova-v1 y genera la firma estadística
de distancias a las que MIROVA publica detecciones por volcán y sensor.

Fenomeno fisico: cada edificio volcanico tiene una "firma" de distancias
a las que MIROVA retiene pixels anomalos. Depende de donde esta el vent
real, de la geometria bow-tie VIIRS, de la geolocalizacion del sensor.
Esta firma es empirica — no se puede inferir del KML oficial, se extrae
del patron observado de publicaciones.

Uso: regenerar cuando llegue CSV nuevo (mensual), comparar firmas entre
ventanas temporales para detectar drift.

Salidas:
  experiments/26_csv_distance_profile.json  — tabla completa por (volcan, sensor)
  stdout                                      — tabla markdown legible

Columnas output por (volcan, sensor):
  n_detecciones
  d_min, d_p25, d_median, d_p75, d_p95, d_max
  vrp_min, vrp_median, vrp_max
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from statistics import median, quantiles


def load_csv(path: Path) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                vrp = float(r["VRP_MW"])
                dist = float(r["Distancia_km"])
            except (ValueError, KeyError):
                continue
            if vrp <= 0:
                continue  # solo detecciones reales MIROVA
            rows.append({
                "timestamp": r["Fecha_Satelite_UTC"],
                "volcan": r["Volcan"],
                "sensor": r["Sensor"],
                "vrp_mw": vrp,
                "dist_km": dist,
            })
    return rows


def _pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def profile(rows: list) -> dict:
    """Group by (volcan, sensor) and compute distance + VRP stats."""
    groups = {}
    for r in rows:
        key = (r["volcan"], r["sensor"])
        groups.setdefault(key, []).append(r)

    out = {}
    for (vol, sens), items in groups.items():
        dists = [r["dist_km"] for r in items]
        vrps = [r["vrp_mw"] for r in items]
        out.setdefault(vol, {})[sens] = {
            "n": len(items),
            "d_min": min(dists),
            "d_p25": _pct(dists, 0.25),
            "d_median": median(dists),
            "d_p75": _pct(dists, 0.75),
            "d_p95": _pct(dists, 0.95),
            "d_max": max(dists),
            "vrp_min": min(vrps),
            "vrp_median": median(vrps),
            "vrp_max": max(vrps),
        }
    return out


def print_markdown(prof: dict):
    print(f"{'Volcan':<22} {'Sensor':<10} {'N':>5} {'d_med':>6} {'d_p95':>6} {'d_max':>6} {'vrp_med':>8} {'vrp_max':>8}")
    print("-" * 78)
    for vol in sorted(prof.keys()):
        for sens in sorted(prof[vol].keys()):
            s = prof[vol][sens]
            print(f"{vol:<22} {sens:<10} {s['n']:>5} "
                  f"{s['d_median']:>6.2f} {s['d_p95']:>6.2f} {s['d_max']:>6.2f} "
                  f"{s['vrp_median']:>8.3f} {s['vrp_max']:>8.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="21_04_2026 registro_vrp_consolidado.csv")
    ap.add_argument("--out", default="experiments/26_csv_distance_profile.json")
    args = ap.parse_args()

    rows = load_csv(Path(args.csv))
    print(f"Cargadas {len(rows)} detecciones MIROVA con VRP>0 desde {args.csv}\n")
    prof = profile(rows)
    print_markdown(prof)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(prof, open(args.out, "w", encoding="utf-8"), indent=2, default=float)
    print(f"\nPerfil guardado en {args.out}")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
