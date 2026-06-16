"""S111 D11 — caracterización offline read-only del universo MODIS far/summit.

Pregunta adversarial (A62): el gate del ancla (design 2026-06-16) es first_pass_summit>0,
que cubre la vía ctx_cluster. PERO la cascada resolve_honest_anchor también tiene la rama
test1 (test1_triggered → summit). ¿El artefacto NdC tiene vía alternativa a summit vía Test1?
Si muchos records far MODIS de NdC tienen triggered_test1, el gate first_pass_summit sería
INCOMPLETO (Test1 escaparía el gate). Lo verificamos con los JSON actuales.

NO toca pipeline. Solo lee data/mirova_equivalent/*.json. Resumen <500 tokens.
"""
import json, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "mirova_equivalent"
# inner_radius_km oficiales MIROVA (CLAUDE.md reglas geométricas S14)
INNER = {
    "Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0,
    "Lascar": 5.0, "Isluga": 5.0, "NevadosDeChillan": 5.0, "Llaima": 5.0,
    "Villarrica": 5.0, "Chaiten": 5.0, "Tupungatito": 7.0,
    "PuyehueCordonCaulle": 20.0,
}


def is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


def char(vol):
    doc = json.loads((DATA / f"{vol}.json").read_text(encoding="utf-8"))
    recs = doc["records"] if isinstance(doc, dict) else doc
    modis = [r for r in recs if is_modis(r)]
    inner = INNER[vol]
    # campos relevantes
    far = [r for r in modis if r.get("distance_class") == "far"]
    summit = [r for r in modis if r.get("distance_class") == "summit"]
    none_cls = [r for r in modis if r.get("distance_class") not in ("far", "summit")]

    def pc_dist(r):
        pc = r.get("primary_cluster") or {}
        return pc.get("centroid_dist_km")

    # records far con cluster cercano (<=inner) = candidatos a flip si ancla ON-sin-gate
    far_cluster_near = [r for r in far if (pc_dist(r) is not None and pc_dist(r) <= inner)]
    # de esos, ¿cuántos tienen triggered_test1 (vía alternativa a summit)?
    far_near_test1 = [r for r in far_cluster_near if r.get("triggered_test1")]
    # ¿cuántos tienen first-pass total > 0? (proxy grueso, NO summit-restricted)
    far_near_fp0 = [r for r in far_cluster_near if (r.get("diag_n_first_pass_pixels") or 0) == 0]
    far_near_recap = [r for r in far_cluster_near
                      if (r.get("diag_n_second_pass_recapture") or 0) > 0]

    print(f"\n=== {vol} (inner={inner} km) ===", flush=True)
    print(f"  MODIS records: {len(modis)}  | far={len(far)} summit={len(summit)} "
          f"otro={len(none_cls)}", flush=True)
    print(f"  far con cluster cercano (<= inner, candidatos flip si ancla sin gate): "
          f"{len(far_cluster_near)}", flush=True)
    print(f"    de esos triggered_test1 (VÍA ALTERNATIVA a summit, riesgo gate): "
          f"{len(far_near_test1)}", flush=True)
    print(f"    de esos diag_n_first_pass_pixels==0 (total scene-wide): {len(far_near_fp0)}", flush=True)
    print(f"    de esos con second_pass_recapture>0: {len(far_near_recap)}", flush=True)
    # también: summit actuales con triggered_test1 (para no romper cat-b real)
    summit_test1 = [r for r in summit if r.get("triggered_test1")]
    print(f"  summit actuales: {len(summit)} (de esos triggered_test1={len(summit_test1)})", flush=True)
    # fuentes finales actuales (ancla MODIS OFF → cascada legacy)
    from collections import Counter
    srcs = Counter(r.get("final_hotspot_source") for r in modis)
    print(f"  final_hotspot_source (MODIS, ancla OFF): {dict(srcs)}", flush=True)


if __name__ == "__main__":
    for v in INNER:
        try:
            char(v)
        except FileNotFoundError:
            print(f"\n=== {v} === (sin JSON)", flush=True)
