"""S108 — Probe OFFLINE del destape del ancla honesta MODIS (espejo probe_v750_destape).

Cuantifica, sobre data base (flip OFF), cuántos records MODIS pasarían far->summit si
se activara `enable_honest_anchor_modis` (la posición honesta = cluster contextual al
cráter en vez del píxel suelto del Salar, D12). Separa:
  - CURA del recall: flips far->summit con pc.vrp<=5 Y MIROVA publicó (TP recuperado).
  - LANDMINE: flips far->summit con pc.vrp>5 (inflados de método; los cura §2 V-B).

Caveat A18: el probe offline NO predice cluster selection real (el reproc rerunnea
desde cero). Da DIRECCIÓN + orden de magnitud, no el conteo exacto (probe V750 dio
93 vs 32 real). Para el conteo real: reproc con el flag ON.

Uso: python experiments/_s107_modis_localmag/probe_modis_destape.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Lascar": 5,
         "Isluga": 5, "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5,
         "Chaiten": 5, "Tupungatito": 7, "PuyehueCordonCaulle": 20}


def modis(vol):
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    recs = obj.get("records", obj)
    return [r for r in recs if str(r.get("sensor", "")).startswith("MODIS")]


def alert_nights(vol):
    out = set()
    for row in csv.DictReader(open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace")):
        if row.get("Volcan") == vol and str(row.get("Tipo_Registro", "")).startswith("ALERTA_TERMICA"):
            out.add((row.get("Fecha_Satelite_UTC") or "")[:10])
    return out


def main():
    print(f"{'vol':<20}{'nMODIS':>7}{'far':>6}{'flips f->s':>11}{'cura(MIROVA,≤5)':>16}"
          f"{'landmine(>5)':>13}{'max vrp flip':>13}")
    T = {"flips": 0, "cura": 0, "land": 0}
    for vol in VOLS:
        recs = modis(vol)
        inner = INNER[vol]
        nights = alert_nights(vol)
        flips, far = [], 0
        for r in recs:
            dc = r.get("distance_class")
            if dc == "far":
                far += 1
            pc = r.get("primary_cluster") or {}
            src = r.get("final_hotspot_source")
            if src == "test1" or (r.get("triggered_test1") and not (r.get("anomaly_pixels") or [])):
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
        cura = [r for r in flips
                if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) <= 5
                and (r.get("datetime_utc") or "")[:10] in nights]
        land = [r for r in flips if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 5]
        vrps = [((r.get("primary_cluster") or {}).get("vrp_mw") or 0) for r in flips]
        T["flips"] += len(flips); T["cura"] += len(cura); T["land"] += len(land)
        mx = f"{max(vrps):.1f}" if vrps else "—"
        print(f"{vol:<20}{len(recs):>7}{far:>6}{len(flips):>11}{len(cura):>16}"
              f"{len(land):>13}{mx:>13}")
    print(f"\nTOTAL flips far->summit={T['flips']} | cura recall(MIROVA,≤5)={T['cura']} "
          f"| landmine(>5, los cura §2 V-B)={T['land']}")
    print("Lectura: 'cura' = TP MODIS recuperados (suben recall summit-gated, hoy 10.8%). "
          "'landmine' = inflados que el flip destaparía como summit -> §2 V-B debe curarlos "
          "ANTES del flip (por eso §1 ancla y §2 magnitud están acoplados). A18: orden de "
          "magnitud, no exacto.")


if __name__ == "__main__":
    main()
