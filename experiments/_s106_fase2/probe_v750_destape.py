"""S106 — ¿Activar el ancla honesta en VIIRS750 destapa records inflados?

Mismo riesgo que MODIS (design 2026-06-11 §3.3): hoy el distance_class de V750
deriva del campo corrupto; si records con pc.vrp alto están clasificados "far"
por accidente y el ancla honesta los reclasifica "summit", el dashboard los
mostraría. Simula la cascada honesta offline sobre data/mirova_equivalent:

  ancla simulada = pc.centroid (proxy del ctx_cluster: con first-pass ON el pc
  de records no-test1 ES el cluster contextual) | test1-src -> vent (dist 0).

Cuenta los flips far->summit y la distribución de pc.vrp de esos records
(umbral de atención: pc.vrp > 5 MW, como los 132 de MODIS) + cruce MIROVA.

Uso: python probe_v750_destape.py
"""
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Lascar": 5,
         "Isluga": 5, "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5,
         "Chaiten": 5, "Tupungatito": 7, "PuyehueCordonCaulle": 20}


def v750(vol):
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json",
                         encoding="utf-8"))
    recs = obj.get("records", obj)
    return [r for r in recs if str(r.get("sensor", "")).endswith("750")]


def alert_nights(vol):
    out = set()
    rows = csv.DictReader(open(ROOT / "latest_consolidado.csv",
                               encoding="utf-8", errors="replace"))
    for row in rows:
        if row["Volcan"] == vol and row["Tipo_Registro"] == "ALERTA_TERMICA":
            out.add((row["Fecha_Satelite_UTC"] or "")[:10])
    return out


def main():
    print(f"{'vol':<20}{'nV750':>6}{'far_hoy':>8}{'flips f->s':>11}"
          f"{'flips vrp>5':>12}{'max vrp flip':>13}  flips en noche ALERTA")
    tot_flips = tot_big = 0
    for vol in VOLS:
        recs = v750(vol)
        inner = INNER[vol]
        nights = alert_nights(vol)
        flips, far_today = [], 0
        for r in recs:
            dc = r.get("distance_class")
            if dc == "far":
                far_today += 1
            pc = r.get("primary_cluster") or {}
            # ancla honesta simulada
            if r.get("final_hotspot_source") == "test1" or (
                    r.get("triggered_test1") and not (r.get("anomaly_pixels") or [])):
                new_dist = 0.0
            elif pc.get("centroid_dist_km") is not None:
                new_dist = pc["centroid_dist_km"]
            else:
                new_dist = r.get("final_hotspot_dist_km")
            if new_dist is None:
                continue
            new_dc = "summit" if new_dist <= inner else "far"
            if dc == "far" and new_dc == "summit":
                flips.append(r)
        big = [r for r in flips
               if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 5]
        vrps = [((r.get("primary_cluster") or {}).get("vrp_mw") or 0) for r in flips]
        in_alert = sum(1 for r in flips
                       if (r.get("datetime_utc") or "")[:10] in nights)
        tot_flips += len(flips)
        tot_big += len(big)
        mx = f"{max(vrps):.1f}" if vrps else "—"
        print(f"{vol:<20}{len(recs):>6}{far_today:>8}{len(flips):>11}"
              f"{len(big):>12}{mx:>13}  {in_alert}/{len(flips)}")
    print(f"\nTOTAL flips far->summit: {tot_flips} | con pc.vrp>5MW: {tot_big}")
    print("(comparar con MODIS: 132 records pc.vrp>5 = bloqueo del espejo)")


if __name__ == "__main__":
    main()
