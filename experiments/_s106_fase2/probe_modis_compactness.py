"""S106 — Discriminante de COMPACTEZ para el destape MODIS (design 2026-06-05 §5.2).

Ahora testeable offline: anomaly_pixels se persiste desde S94/S95. Para cada
record MODIS con pc.vrp>0, computa:
  compactness = fracción de la energía total (suma vrp_mw de anomaly_pixels)
                contenida a <= R_CORE km del píxel de máxima energía.
  disp_km     = desviación espacial ponderada por energía (radio RMS al centro
                de masa de energía).

Poblaciones: INFLADOS (pc.vrp>5, 11 vols, 0% MIROVA = artefacto first-pass
warm-blob) vs LASCAR real (~248, calibrado 0.92x) vs NDC-F47 (332 MW real).
Barrido de umbral: % inflados suprimidos vs % real conservado.

Uso: python probe_modis_compactness.py
"""
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
R_CORE_KM = 1.5


def hav(la1, lo1, la2, lo2):
    R, p = 6371.0, math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * math.asin(min(1, math.sqrt(a)))


def modis_recs(vol):
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json",
                         encoding="utf-8"))
    recs = obj.get("records", obj)
    return [r for r in recs if str(r.get("sensor", "")).startswith("MODIS")]


def metrics(r):
    # SOLO los píxeles del cluster primario (anomaly_pixels es SCENE-WIDE en
    # MODIS — incluye FPs a 20 km; sin este recorte la métrica mide la escena,
    # no el cluster — error detectado en la 1ª corrida de este probe).
    pc = r.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    px = [p for p in (r.get("anomaly_pixels") or [])
          if p.get("vrp_mw") and p.get("lat") is not None
          and hav(clat, clon, p["lat"], p["lon"]) <= 3.0]
    if len(px) < 2:
        return None  # 1 píxel = compacto por definición, no discrimina
    tot = sum(p["vrp_mw"] for p in px)
    if tot <= 0:
        return None
    top = max(px, key=lambda p: p["vrp_mw"])
    core = sum(p["vrp_mw"] for p in px
               if hav(top["lat"], top["lon"], p["lat"], p["lon"]) <= R_CORE_KM)
    # centro de masa de energía + radio RMS ponderado
    clat = sum(p["lat"] * p["vrp_mw"] for p in px) / tot
    clon = sum(p["lon"] * p["vrp_mw"] for p in px) / tot
    disp = math.sqrt(sum(p["vrp_mw"] * hav(clat, clon, p["lat"], p["lon"]) ** 2
                         for p in px) / tot)
    return {"compact": core / tot, "disp_km": disp, "n_px": len(px)}


def med(xs):
    return statistics.median(xs) if xs else None


def main():
    inflados, lascar = [], []
    for vol in VOLS:
        for r in modis_recs(vol):
            pc = r.get("primary_cluster") or {}
            if not (pc.get("vrp_mw") or 0) > 0:
                continue
            m = metrics(r)
            entry = (r, m, vol)
            if vol == "Lascar":
                lascar.append(entry)
            if (pc.get("vrp_mw") or 0) > 5:
                inflados.append(entry)

    for name, pop in (("INFLADOS pc>5", inflados), ("LASCAR real", lascar)):
        ms = [m for _, m, _ in pop if m]
        n1px = sum(1 for _, m, _ in pop if m is None)
        print(f"{name:<16} n={len(pop)} (1-px/no-metric: {n1px})  "
              f"compact med={med([x['compact'] for x in ms]):.2f}  "
              f"disp med={med([x['disp_km'] for x in ms]):.2f} km  "
              f"npx med={med([x['n_px'] for x in ms])}")

    print(f"\nBarrido umbral compactness (suprimir si compact < thr; "
          f"1-px siempre conservado):")
    for thr in (0.5, 0.6, 0.7, 0.8, 0.9):
        sup_inf = sum(1 for _, m, _ in inflados if m and m["compact"] < thr)
        keep_las = sum(1 for _, m, _ in lascar
                       if m is None or m["compact"] >= thr)
        print(f"  thr={thr:.1f}: inflados suprimidos {sup_inf}/{len(inflados)}"
              f" ({100*sup_inf/len(inflados):.0f}%) | Lascar conservado"
              f" {keep_las}/{len(lascar)} ({100*keep_las/len(lascar):.0f}%)")

    print(f"\nBarrido umbral dispersion (suprimir si disp > thr):")
    for thr in (0.8, 1.0, 1.5, 2.0):
        sup_inf = sum(1 for _, m, _ in inflados if m and m["disp_km"] > thr)
        keep_las = sum(1 for _, m, _ in lascar
                       if m is None or m["disp_km"] <= thr)
        print(f"  thr={thr:.1f}km: inflados suprimidos {sup_inf}/{len(inflados)}"
              f" ({100*sup_inf/len(inflados):.0f}%) | Lascar conservado"
              f" {keep_las}/{len(lascar)} ({100*keep_las/len(lascar):.0f}%)")


if __name__ == "__main__":
    main()
