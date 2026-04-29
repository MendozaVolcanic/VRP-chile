"""S27 — post-procesa JSONs de data/_mirova_literal/ agregando primary_cluster
con vrp_mw alineado a MIROVA (suma de pixels del cluster geográfico principal).

Razón: el `vrp_mw` de cada record es la suma indistinta de TODOS los pixels
detectados en el granule. MIROVA reporta solo el cluster contiguo principal.
Para comparar magnitudes con CSV consolidado, agregamos el VRP del cluster
geográfico mayor.

Uso:
    python scripts/add_primary_cluster_vrp.py
    # Procesa los 10 Tier A en data/_mirova_literal/ (NdC excluido).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.clustering import cluster_pixels_geographic  # noqa: E402

TIER_A = [
    "Lascar", "Lastarria", "Tupungatito", "Villarrica",
    "PuyehueCordonCaulle", "Copahue", "Llaima",
    "Chaiten", "PlanchonPeteroa", "Isluga",
]


def process_record(rec: dict) -> bool:
    """Agrega/sobrescribe primary_cluster en el record. Retorna True si modificó."""
    pixels = rec.get("anomaly_pixels", [])
    if not pixels:
        return False

    # Filtrar pixels con coords válidas
    valid = [p for p in pixels if p.get("lat") is not None and p.get("lon") is not None]
    if not valid:
        return False

    clusters = cluster_pixels_geographic(valid, max_dist_km=1.5)
    if not clusters:
        return False

    primary = clusters[0]
    rec["primary_cluster"] = {
        "n_pixels": primary["n_pixels"],
        "vrp_mw": round(primary["vrp_mw"], 3),
        "centroid_lat": round(primary["centroid_lat"], 5),
        "centroid_lon": round(primary["centroid_lon"], 5),
    }
    rec["n_hotspots_clustered"] = len(clusters)
    return True


def main():
    src_dir = ROOT / "data" / "_mirova_literal"
    if not src_dir.exists():
        print(f"NO EXISTE: {src_dir}")
        return

    for vol in TIER_A:
        p = src_dir / f"{vol}.json"
        if not p.exists():
            print(f"  {vol:>22}: SKIP (no existe)")
            continue
        raw = json.loads(p.read_text(encoding="utf-8"))
        records = raw["records"] if isinstance(raw, dict) else raw

        n_modified = 0
        for rec in records:
            if process_record(rec):
                n_modified += 1

        # Reescribir
        if isinstance(raw, dict):
            raw["records"] = records
            out = raw
        else:
            out = records
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"  {vol:>22}: {n_modified}/{len(records)} records con primary_cluster")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
