"""S106 — Probe 2 del ancla honesta: candidato = primary_cluster.centroid (vent-anchored).

El probe 1 mostró que el píxel contextual max-vrp NO cura Villarrica/Llaima (mediana
2.86 km) pero SÍ Tupungatito (0.36 km) y Láscar (0.25 km). Acá pruebo el candidato
del fix §2.1: el centroide del primary_cluster (la selección vent-anchored que ya
existe), y desgloso el porqué del caso Villarrica/Llaima: rumbo de los píxeles
contextuales (A70) y qué pasa en noches ALERTA vs noches comunes.

Uso: python probe_anchor_design2.py
"""
import csv
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375, hav, VENT

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]


def alert_nights_v375(vol):
    out = set()
    rows = csv.DictReader(open(ROOT / "latest_consolidado.csv",
                               encoding="utf-8", errors="replace"))
    for r in rows:
        if (r["Volcan"] == vol and r["Tipo_Registro"] == "ALERTA_TERMICA"
                and r["Sensor"] == "VIIRS375"):
            day = (r["Fecha_Satelite_UTC"] or "")[:10]
            if day:
                out.add(day)
    return out


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, spec=".0f"):
    return format(x, spec) if x is not None else "—"


def rumbo(dlat_m, dlon_m):
    ang = math.degrees(math.atan2(dlon_m, dlat_m)) % 360
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((ang + 22.5) // 45) % 8]


def main():
    for vol in VOLS:
        vlat, vlon = VENT[vol]
        recs = v375(load(BASE / "baseline_mir", vol))
        nights = alert_nights_v375(vol)

        with_pc = [r for r in recs if (r.get("primary_cluster") or {}).get("centroid_lat") is not None]
        offN_pc, dist_pc = [], []
        for r in with_pc:
            pc = r["primary_cluster"]
            offN_pc.append((pc["centroid_lat"] - vlat) * 111320)
            dist_pc.append(hav(vlat, vlon, pc["centroid_lat"], pc["centroid_lon"]))

        offN_cur = [(r["final_hotspot_lat"] - vlat) * 111320
                    for r in recs if r.get("final_hotspot_lat") is not None]
        dist_cur = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])
                    for r in recs if r.get("final_hotspot_lat") is not None]

        # rumbos de los pixeles contextuales (todos los anomaly_pixels)
        rumbos = Counter()
        for r in recs:
            for px in (r.get("anomaly_pixels") or []):
                rumbos[rumbo((px["lat"] - vlat) * 111320,
                             (px["lon"] - vlon) * 111320 *
                             math.cos(math.radians(vlat)))] += 1

        # noches ALERTA: dist del pc en esas noches (la posicion "real" candidata)
        dist_pc_alert = []
        for r in with_pc:
            if (r.get("datetime_utc") or "")[:10] in nights:
                pc = r["primary_cluster"]
                dist_pc_alert.append(hav(vlat, vlon, pc["centroid_lat"], pc["centroid_lon"]))

        print(f"\n=== {vol} ===")
        print(f"  records con primary_cluster: {len(with_pc)}/{len(recs)}")
        print(f"  ancla ACTUAL (final_hotspot): offN={fmt(med(offN_cur))} m"
              f"  dist={fmt(med(dist_cur), '.2f')} km")
        print(f"  candidato PC centroid:        offN={fmt(med(offN_pc))} m"
              f"  dist={fmt(med(dist_pc), '.2f')} km")
        print(f"  PC centroid SOLO noches ALERTA: dist={fmt(med(dist_pc_alert), '.2f')} km"
              f"  (n={len(dist_pc_alert)})")
        print(f"  rumbos pixeles contextuales: {dict(rumbos.most_common())}")


if __name__ == "__main__":
    main()
