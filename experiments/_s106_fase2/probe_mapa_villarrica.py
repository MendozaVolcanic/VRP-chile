"""S106 — ¿Qué son los puntos que quedan lejos del cráter en el mapa de Villarrica?

Replica la lógica de marker primario del frontend post-#403 sobre la data servida,
por SENSOR (el ancla honesta solo está viva en VIIRS375; V750/MODIS flag-OFF), y
cruza cada record contra las noches ALERTA VIIRS375/VIIRS/MODIS de MIROVA.

Uso: python probe_mapa_villarrica.py
"""
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOL = "Villarrica"
VLAT, VLON = -39.420227, -71.939876


def hav(la1, lo1, la2, lo2):
    R, p = 6371.0, math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * math.asin(min(1, math.sqrt(a)))


def sensor_bucket(s):
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("750"):
        return "VIIRS750"
    return "VIIRS375"


def marker(r):
    """Marker primario como lo pinta index.html post-#403."""
    honest = (r.get("final_hotspot_lat") is not None
              and r.get("final_hotspot_source") in ("test1_roi", "test1_nti_peak"))
    if honest:
        return r["final_hotspot_lat"], r["final_hotspot_lon"], "honest"
    ap = r.get("anomaly_pixels") or []
    if ap:
        return ap[0]["lat"], ap[0]["lon"], "px0"
    if r.get("final_hotspot_lat") is not None:
        return r["final_hotspot_lat"], r["final_hotspot_lon"], "final"
    return None


def alert_nights():
    out = defaultdict(set)
    rows = csv.DictReader(open(ROOT / "latest_consolidado.csv",
                               encoding="utf-8", errors="replace"))
    for row in rows:
        if row["Volcan"] == VOL and row["Tipo_Registro"] == "ALERTA_TERMICA":
            out[row["Sensor"]].add((row["Fecha_Satelite_UTC"] or "")[:10])
    return out


def main():
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{VOL}.json",
                         encoding="utf-8"))
    recs = obj.get("records", obj)
    nights = alert_nights()
    n_all_mirova = set().union(*nights.values()) if nights else set()

    print(f"{'sensor':<10}{'n':>5}{'dist med':>9}{'<=1km':>7}{'>1km':>6}"
          f"{'%>1km':>7}  noches: en-ALERTA-MIROVA / total-noches")
    far_sources = Counter()
    for bucket in ("VIIRS375", "VIIRS750", "MODIS"):
        sel = [r for r in recs if sensor_bucket(r.get("sensor", "")) == bucket]
        ms = [(r, marker(r)) for r in sel]
        ms = [(r, m) for r, m in ms if m]
        dists = [(r, hav(VLAT, VLON, m[0], m[1]), m[2]) for r, m in ms]
        if not dists:
            continue
        dvals = [d for _, d, _ in dists]
        near = sum(1 for d in dvals if d <= 1.0)
        far = [(r, d, src) for r, d, src in dists if d > 1.0]
        rec_nights = {(r.get("datetime_utc") or "")[:10] for r, _, _ in dists}
        far_nights = {(r.get("datetime_utc") or "")[:10] for r, _, _ in far}
        in_alert = len(rec_nights & n_all_mirova)
        far_in_alert = len(far_nights & n_all_mirova)
        for r, d, src in far:
            far_sources[(bucket, src)] += 1
        print(f"{bucket:<10}{len(dvals):>5}{statistics.median(dvals):>9.2f}"
              f"{near:>7}{len(far):>6}{100*len(far)/len(dvals):>6.0f}%"
              f"  {in_alert}/{len(rec_nights)} noches con marker"
              f" | far en noche ALERTA: {far_in_alert}/{len(far_nights)}")

    print(f"\nNoches ALERTA MIROVA {VOL} (CSV): "
          + ", ".join(f"{k}:{len(v)}" for k, v in nights.items()))
    print(f"Fuente de los markers >1km: {dict(far_sources)}")


if __name__ == "__main__":
    main()
