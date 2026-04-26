"""S23 T14 — Factor 42 clustering test: MIROVA agrupa pixels contiguos?

Hipótesis (audit S22): cuando MIROVA reporta 1 hotspot, internamente puede ser
que múltiples pixels VIIRS contiguos hayan disparado pero los agrupó en un
cluster único. Nuestro pipeline cuenta cada pixel individual.

Caso canónico: Lascar 2025-11-15 — 77 px nuestro vs 4 reportados MIROVA.

Test: aplicar `scipy.ndimage.label` con conectividad 4-vecinos y 8-vecinos
sobre nuestros records con muchos pixels. Si los 77 px de Lascar se agrupan
en ~4 clusters, hipótesis confirmada (MIROVA reporta clusters).

Uso:
    python experiments/50_factor_42_clustering_test.py
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


def cluster_pixels_by_distance(pixels: list[dict], cluster_radius_km: float = 1.5) -> int:
    """Conteo de clusters: pixels dentro de cluster_radius_km del mismo cluster.

    Implementa unión-find simple: para cada pixel, juntar con cualquier otro
    dentro del radio. Retorna número de clusters resultantes.
    """
    if len(pixels) <= 1:
        return len(pixels)

    n = len(pixels)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def haversine_pixel(p, q):
        lat1, lon1 = p["lat"], p["lon"]
        lat2, lon2 = q["lat"], q["lon"]
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(min(1, a)))

    for i in range(n):
        for j in range(i + 1, n):
            if haversine_pixel(pixels[i], pixels[j]) <= cluster_radius_km:
                union(i, j)

    return len(set(find(i) for i in range(n)))


def find_records_with_many_pixels(volcano: str, threshold: int = 50,
                                   max_results: int = 10) -> list[dict]:
    """Records con n_anomaly_pixels >= threshold. Útil para test factor 42."""
    d = json.loads(Path(f"data/mirova_equivalent/{volcano}.json").read_text(encoding="utf-8"))
    found = []
    for rec in d.get("records", []):
        px = rec.get("anomaly_pixels") or []
        if len(px) >= threshold:
            found.append({
                "datetime_utc": rec.get("datetime_utc"),
                "sensor": rec.get("sensor"),
                "n_pixels": len(px),
                "pixels": px,
                "vrp_mw": rec.get("vrp_mw") or 0,
            })
        if len(found) >= max_results:
            break
    return found


def main():
    print("=" * 70)
    print("S23 T14 — Factor 42 clustering test")
    print("=" * 70)
    print()

    for vol in ["Lascar", "Tupungatito", "Lastarria", "Chaiten"]:
        records_many_px = find_records_with_many_pixels(vol, threshold=50,
                                                          max_results=5)
        if not records_many_px:
            print(f"[{vol}] sin records con >50 pixels")
            continue
        print(f"[{vol}] {len(records_many_px)} records con >50 pixels:")
        for rec in records_many_px:
            n = rec["n_pixels"]
            for cluster_radius_km in [0.5, 1.0, 1.5, 2.0]:
                n_clusters = cluster_pixels_by_distance(rec["pixels"],
                                                        cluster_radius_km)
                ratio = n / n_clusters if n_clusters else float("nan")
                print(f"  {rec['datetime_utc']} {rec['sensor']:25} "
                      f"n_px={n:4d}  cluster@{cluster_radius_km}km={n_clusters:3d}  "
                      f"ratio_px_per_cluster={ratio:.1f}")
            print()

    print("=" * 70)
    print("Interpretacion:")
    print("- Si ratio px/cluster ~ 10-50, MIROVA probable agrupa contiguos.")
    print("- Si ratio ~ 1, los pixels NO son contiguos (factor 42 NO es clustering).")
    print("- cluster_radius mas grande -> menos clusters -> ratio mas alto.")


if __name__ == "__main__":
    main()
