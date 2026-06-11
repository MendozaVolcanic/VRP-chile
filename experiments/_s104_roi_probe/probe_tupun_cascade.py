"""S106 — ¿Por qué Tupungatito ancla por Test1 si su cluster está a 0.36 km?

Hipótesis: la cascada Regla D (test1 summit + eruption far -> gana test1) se dispara
porque el ancla "eruption" usa el píxel suelto scene-wide (bug §2.1) que SÍ está far,
aunque el primary_cluster esté pegado al cráter. Si es así, el fix §2.1 (eruption
ancla = pc.centroid) cura el sesgo de posición de Tupungatito SIN tocar el Test1.

Mide en baseline_mir/Tupungatito (VIIRS375): distribución de final_hotspot_source;
y para los src=test1: dónde estaba el píxel suelto (hotspot_dist_km) vs el cluster
(pc.centroid_dist_km) vs el inner_radius (7 km Tupungatito).

Uso: python probe_tupun_cascade.py
"""
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375

BASE = Path(__file__).parent
INNER_KM = 7.0  # Tupungatito


def med(xs):
    return statistics.median(xs) if xs else None


def main():
    recs = v375(load(BASE / "baseline_mir", "Tupungatito"))
    print("final_hotspot_source:", Counter(r.get("final_hotspot_source")
                                           for r in recs).most_common())
    t1 = [r for r in recs if r.get("final_hotspot_source") == "test1"]
    hs = [r.get("hotspot_dist_km") for r in t1 if r.get("hotspot_dist_km") is not None]
    pc = [(r.get("primary_cluster") or {}).get("centroid_dist_km") for r in t1]
    pc = [x for x in pc if x is not None]
    far = sum(1 for x in hs if x > INNER_KM)
    pc_near = sum(1 for x in pc if x <= INNER_KM)
    print(f"\nsrc=test1: n={len(t1)}")
    print(f"  pixel suelto scene-wide: dist mediana={med(hs):.2f} km | far(>7km): {far}/{len(hs)}")
    print(f"  primary_cluster:         dist mediana={med(pc):.2f} km | summit(<=7km): {pc_near}/{len(pc)}")
    fh = [r.get("final_hotspot_dist_km") for r in t1 if r.get("final_hotspot_dist_km") is not None]
    print(f"  final_hotspot (test1 centroid): dist mediana={med(fh):.2f} km")


if __name__ == "__main__":
    main()
