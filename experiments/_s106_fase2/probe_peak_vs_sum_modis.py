"""S106 — ¿La magnitud MODIS inflada se cura tomando el PÍXEL PICO en vez de la
SUMA del cluster? (lever testeable offline con anomaly_pixels persistidos).

Mecanismo verificado (no asumido): los 132 inflados son first-pass/eruption
(116 eruption, 11 test1) — NO los cura ctxpeak (gateado source=test1). El cluster
(11 px med) suma muchos px marginales sobre fondo regional frío. MIROVA reporta
estos "<5 MW". Candidato: magnitud = px pico (o top-k) en vez de suma del cluster.

Aproxima la magnitud del cluster por la suma de los anomaly_pixels DENTRO de 3 km
del centroide del cluster (proxy del cluster contiguo), y compara:
  sum_cluster (actual) vs peak_pixel vs top3.
Poblaciones: INFLADOS (pc.vrp>5, 0% MIROVA) vs LASCAR real (calibrado 0.92x).

Uso: python probe_peak_vs_sum_modis.py
"""
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]


def hav(la1, lo1, la2, lo2):
    R, p = 6371.0, math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * math.asin(min(1, math.sqrt(a)))


def cluster_pixels(r):
    pc = r.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    px = [p for p in (r.get("anomaly_pixels") or [])
          if p.get("vrp_mw") and p.get("lat") is not None
          and hav(clat, clon, p["lat"], p["lon"]) <= 3.0]
    return px or None


def variants(px):
    vrps = sorted((p["vrp_mw"] for p in px), reverse=True)
    return {"sum": sum(vrps), "peak": vrps[0], "top3": sum(vrps[:3])}


def med(xs):
    return statistics.median(xs) if xs else None


def main():
    inf, las = [], []
    for vol in VOLS:
        obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json",
                             encoding="utf-8"))
        for r in obj.get("records", obj):
            if not str(r.get("sensor", "")).startswith("MODIS"):
                continue
            pc = r.get("primary_cluster") or {}
            if not (pc.get("vrp_mw") or 0) > 0:
                continue
            px = cluster_pixels(r)
            if not px:
                continue
            v = variants(px)
            if (pc.get("vrp_mw") or 0) > 5:
                inf.append(v)
            if vol == "Lascar":
                las.append(v)

    print(f"{'pop':<16}{'n':>5}{'sum med':>9}{'peak med':>10}{'top3 med':>10}")
    for name, pop in (("INFLADOS pc>5", inf), ("LASCAR real", las)):
        print(f"{name:<16}{len(pop):>5}{med([v['sum'] for v in pop]):>9.2f}"
              f"{med([v['peak'] for v in pop]):>10.2f}{med([v['top3'] for v in pop]):>10.2f}")

    print("\nSi magnitud = PEAK: ¿cuántos inflados caen <5 MW y cuánto baja Lascar real?")
    for variant in ("peak", "top3"):
        inf_cured = sum(1 for v in inf if v[variant] <= 5)
        # Lascar real: cuánto de su señal real se conserva (ratio variant/sum)
        las_ratio = med([v[variant] / v["sum"] for v in las if v["sum"] > 0])
        las_loss = med([(v["sum"] - v[variant]) for v in las])
        print(f"  {variant:<5}: inflados curados <5MW {inf_cured}/{len(inf)} "
              f"({100*inf_cured/len(inf):.0f}%) | Lascar conserva {100*las_ratio:.0f}% "
              f"de su magnitud (pierde {las_loss:.2f} MW med)")


if __name__ == "__main__":
    main()
