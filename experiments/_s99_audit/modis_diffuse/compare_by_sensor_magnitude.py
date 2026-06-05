"""S101 — Comparación de magnitud NUESTRA vs MIROVA POR SENSOR (auditoría dashboard).

Observación Nicolás: el Diario grafica MIROVA NRT como UNA serie (max diario across
sensores) mientras nuestras series van por sensor → comparación injusta. Acá comparo
sensor-a-sensor: por (vol, día, sensor) máx diario nuestro vs MIROVA del MISMO sensor,
ventana 90d. Muestra que VIIRS375 (ya curado) se parece a MIROVA-VIIRS375, y que la
disimilitud está en MODIS/VIIRS750 (sec³, frente pendiente).

Buckets MIROVA CSV: 'MODIS','VIIRS375','VIIRS'(=M-band 750). Nuestro: MODIS_*,
VIIRS_{SNPP,NOAA20,NOAA21}=375, VIIRS_*_750. Fuente S91: este script.
"""
import json, csv, statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica", "Llaima",
        "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria", "NevadosDeChillan"]
namemap = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "NevadosDeChillan": "Nevados de Chillan"}
INNER = {'Lascar': 5, 'PuyehueCordonCaulle': 20, 'Tupungatito': 7, 'Chaiten': 5, 'Villarrica': 5,
         'Llaima': 5, 'PlanchonPeteroa': 3, 'Copahue': 4, 'Isluga': 5, 'Lastarria': 3, 'NevadosDeChillan': 5}
# ventana 90d desde "hoy" del dataset (usar 2026-06-05 como ancla, pasado por contexto)
TODAY = date(2026, 6, 5)
CUTOFF = (TODAY - timedelta(days=90)).isoformat()


def our_bucket(s):
    s = (s or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def eqvrp(r, inner):
    pc = r.get("primary_cluster") or {}
    cd = pc.get("centroid_dist_km")
    summit = (r.get("distance_class") == "summit") or (cd is not None and cd <= inner)
    return (pc.get("vrp_mw", 0) or 0) if summit else 0


# MIROVA por (vol, dia, bucket) -> max vrp
mir = defaultdict(lambda: defaultdict(float))
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Tipo_Registro"] != "ALERTA_TERMICA" or r["Sensor"] not in ("MODIS", "VIIRS375", "VIIRS"):
        continue
    day = r["Fecha_Satelite_UTC"][:10]
    if day < CUTOFF:
        continue
    try:
        v = float(r["VRP_MW"])
    except ValueError:
        continue
    mir[(r["Volcan"], day)][r["Sensor"]] = max(mir[(r["Volcan"], day)][r["Sensor"]], v)

print(f"=== Ratio magnitud NUESTRA/MIROVA por sensor (días matcheados, 90d desde {TODAY}) ===\n")
print(f"{'Volcan':<20}{'MODIS':>14}{'VIIRS750':>14}{'VIIRS375':>14}")
out = {}
agg = defaultdict(list)
for vol in VOLS:
    p = REPO / "data/mirova_equivalent" / f"{vol}.json"
    if not p.exists():
        continue
    o = json.load(open(p, encoding="utf-8"))
    inner = INNER[vol]
    mname = namemap.get(vol, vol)
    # nuestro max diario por (dia, bucket)
    ourd = defaultdict(float)
    for r in (o["records"] if isinstance(o, dict) else o):
        day = str(r.get("datetime_utc", ""))[:10]
        if day < CUTOFF:
            continue
        b = our_bucket(r.get("sensor", ""))
        if b is None:
            continue
        ourd[(day, b)] = max(ourd[(day, b)], eqvrp(r, inner))
    # ratios por sensor
    mirbucket = {"MODIS": "MODIS", "VIIRS": "VIIRS", "VIIRS375": "VIIRS375"}
    cells = {}
    for ob, mb in [("MODIS", "MODIS"), ("VIIRS", "VIIRS"), ("VIIRS375", "VIIRS375")]:
        ratios = []
        for (vname, day), sens in mir.items():
            if vname != mname or mb not in sens or sens[mb] <= 0:
                continue
            ours = ourd.get((day, ob), 0)
            if ours > 0:
                ratios.append(ours / sens[mb]); agg[ob].append(ours / sens[mb])
        cells[ob] = (round(statistics.median(ratios), 2), len(ratios)) if ratios else (None, 0)
    out[vol] = cells
    def fmt(c):
        return f"{c[0]}×(n{c[1]})" if c[0] is not None else "-"
    print(f"{vol:<20}{fmt(cells['MODIS']):>14}{fmt(cells['VIIRS']):>14}{fmt(cells['VIIRS375']):>14}")

print("\n=== Mediana global del ratio por sensor (cuán cerca de 1.0 = MIROVA) ===")
for b, lbl in [("MODIS", "MODIS"), ("VIIRS", "VIIRS750"), ("VIIRS375", "VIIRS375")]:
    if agg[b]:
        print(f"  {lbl:<10} ratio mediana={statistics.median(agg[b]):.2f} (n={len(agg[b])})")
print("\nLectura: VIIRS375 cerca de 1.0 = ya clona MIROVA. MODIS/VIIRS750 >>1 = inflados")
print("por sec³ (frente pendiente). La comparación POR SENSOR es la justa (no la agregada).")
json.dump({k: {b: c for b, c in v.items()} for k, v in out.items()},
          open(Path(__file__).parent / "compare_by_sensor_result.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False, default=str)
print("-> compare_by_sensor_result.json")
