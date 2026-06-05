"""S101 — Recalibración de umbrales de filtros display para data nadir-fijo (A16).

Los filtros isCirrusArtifact (VRP>10) e isDiffuseFieldArtifact (VRP>=50) tienen
umbrales calibrados con la magnitud inflada por sec³. Con nadir-fijo la magnitud baja
→ hay que bajar los umbrales para mantener la cobertura, SIN atrapar reales (criterio
sagrado: 0 records MIROVA-confirmados ocultados).

Barre umbrales candidatos y reporta, sobre la data nadir (11 vols):
  - artefactos atrapados (records SIN MIROVA, t_max frío, MODIS) = bueno
  - reales atrapados (records MIROVA-confirmados que el filtro ocultaría) = MALO (FN display)
Elegir el umbral más bajo con reales_atrapados=0 y máxima cobertura de artefactos.

Uso (tras descargar la data nadir):
  gh run download 27022484062 -D experiments/_s99_audit/_nadir_val_art
  python experiments/_s99_audit/modis_diffuse/recalibrate_display_filters.py
Fuente S91: este script. Output stdout + JSON.
"""
import json, csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "experiments/_s99_audit/_nadir_val_art"
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica", "Llaima",
        "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria", "NevadosDeChillan"]
namemap = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "NevadosDeChillan": "Nevados de Chillan"}
INNER = {'Lascar': 5, 'PuyehueCordonCaulle': 20, 'Tupungatito': 7, 'Chaiten': 5, 'Villarrica': 5,
         'Llaima': 5, 'PlanchonPeteroa': 3, 'Copahue': 4, 'Isluga': 5, 'Lastarria': 3, 'NevadosDeChillan': 5}
CIRRUS_CAND = [10, 7, 5, 3, 2]
DIFFUSE_CAND = [50, 30, 20, 12, 8]


def load(vol):
    f = ART / f"nadir-val-{vol}" / f"{vol}.json"
    if not f.exists():
        return None
    o = json.load(open(f, encoding="utf-8"))
    return [r for r in (o["records"] if isinstance(o, dict) else o) if r.get("sensor", "").startswith("MODIS")]


def eqvrp(r, inner):
    """Aprox de mirovaEqVrp: pc.vrp si summit, else 0."""
    pc = r.get("primary_cluster") or {}
    cd = pc.get("centroid_dist_km")
    summit = (r.get("distance_class") == "summit") or (cd is not None and cd <= inner)
    return (pc.get("vrp_mw", 0) or 0) if summit else 0


# MIROVA MODIS confirmados
mir = defaultdict(set)
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA":
        mir[r["Volcan"]].add(r["Fecha_Satelite_UTC"][:10])

# Juntar todos los records con su flag confirmado + t_max + eqvrp + n_px
recs = []
missing = []
for vol in VOLS:
    rs = load(vol)
    if rs is None:
        missing.append(vol); continue
    inner = INNER[vol]
    mname = namemap.get(vol, vol)
    for r in rs:
        day = str(r.get("datetime_utc", ""))[:10]
        recs.append({
            "vol": vol, "tmax": r.get("t_max_k"), "eq": eqvrp(r, inner),
            "npx": (r.get("primary_cluster") or {}).get("n_pixels", 0) or 0,
            "conf": day in mir.get(mname, set()),
        })
if missing:
    print(f"FALTAN artifacts: {missing}\n")

print(f"Records MODIS nadir cargados: {len(recs)}\n")
print("=== isCirrusArtifact: umbral VRP (t_max<273.15) ===")
print(f"{'umbral':>7}{'artef atrapados':>16}{'REALES atrapados (FN)':>22}")
for thr in CIRRUS_CAND:
    art = sum(1 for r in recs if not r["conf"] and r["tmax"] is not None and r["tmax"] < 273.15 and r["eq"] > thr)
    real = sum(1 for r in recs if r["conf"] and r["tmax"] is not None and r["tmax"] < 273.15 and r["eq"] > thr)
    print(f"{thr:>7}{art:>16}{real:>22}{'  <-- FN!' if real else ''}")

print("\n=== isDiffuseFieldArtifact: umbral VRP (t_max<278.15, npx>=100, eq/npx<1) ===")
print(f"{'umbral':>7}{'artef atrapados':>16}{'REALES atrapados (FN)':>22}")
for thr in DIFFUSE_CAND:
    def hit(r, t):
        return (r["tmax"] is not None and r["tmax"] < 278.15 and r["npx"] >= 100
                and r["eq"] >= t and (r["eq"] / max(r["npx"], 1)) < 1.0)
    art = sum(1 for r in recs if not r["conf"] and hit(r, thr))
    real = sum(1 for r in recs if r["conf"] and hit(r, thr))
    print(f"{thr:>7}{art:>16}{real:>22}{'  <-- FN!' if real else ''}")

print("\nElegir: umbral más BAJO con REALES atrapados=0 (criterio sagrado) y máx artefactos.")
print("Replicar el valor elegido en index/diario/mosaico (S92 L5). Luego A45 para el flag nadir.")
