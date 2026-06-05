"""S101 — Rendimiento por sensor vs MIROVA (dato para el paper). Verifica/actualiza S94.

Recall por sensor: de los (volcán, día) que MIROVA detectó en un bucket de sensor,
cuántos detectamos nosotros en el mismo bucket (mismo día, pc.vrp>0). Cuantifica que
VIIRS375 es el caballo operativo y MODIS es casi ciego a estos focos sub-píxel andinos.

Buckets (convención A48): MIROVA 'VIIRS375' ↔ nuestro VIIRS_{SNPP,NOAA20,NOAA21};
MIROVA 'VIIRS' (M-band) ↔ nuestro VIIRS_*_750; MIROVA 'MODIS' ↔ MODIS_*.
Fuente S91: este script. Output stdout + JSON.
"""
import json, csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica", "Llaima",
        "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria", "NevadosDeChillan"]
namemap = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "NevadosDeChillan": "Nevados de Chillan"}
rev = {v: k for k, v in namemap.items()}


def our_bucket(s):
    s = (s or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS"      # M-band 750 ↔ MIROVA 'VIIRS'
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


# MIROVA detecciones por (vol_local, dia, bucket)
mir = defaultdict(set)  # bucket -> set de (vol_local, dia)
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Tipo_Registro"] != "ALERTA_TERMICA":
        continue
    b = r["Sensor"]
    if b not in ("MODIS", "VIIRS375", "VIIRS"):
        continue
    vol_local = rev.get(r["Volcan"], r["Volcan"])
    if vol_local not in VOLS:
        continue
    mir[b].add((vol_local, r["Fecha_Satelite_UTC"][:10]))

# Nuestras detecciones por (vol, dia, bucket)
ours = defaultdict(set)
for vol in VOLS:
    p = REPO / "data/mirova_equivalent" / f"{vol}.json"
    if not p.exists():
        continue
    o = json.load(open(p, encoding="utf-8"))
    for r in (o["records"] if isinstance(o, dict) else o):
        b = our_bucket(r.get("sensor", ""))
        if b is None:
            continue
        if ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0:
            ours[b].add((vol, str(r.get("datetime_utc", ""))[:10]))

print("=== Recall + Precisión por sensor vs MIROVA (días-volcán, 11 Tier A) ===\n")
print(f"{'Bucket':<12}{'MIROVA':>8}{'OURS':>7}{'TP':>6}{'recall':>9}{'precis':>9}")
out = {}
for b in ["VIIRS375", "VIIRS", "MODIS"]:
    miro = mir[b]
    nours = len(ours[b])
    tp = sum(1 for k in miro if k in ours[b])
    tp_o = sum(1 for k in ours[b] if k in miro)  # de nuestras, cuántas MIROVA confirma
    rec = tp / len(miro) if miro else 0
    prec = tp_o / nours if nours else 0
    label = {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750", "MODIS": "MODIS"}[b]
    print(f"{label:<12}{len(miro):>8}{nours:>7}{tp:>6}{rec*100:>8.1f}%{prec*100:>8.1f}%")
    out[label] = {"mirova": len(miro), "ours": nours, "tp": tp, "recall": round(rec, 3),
                  "precision": round(prec, 3)}
print("\nNota (A54): precisión cruda baja en VIIRS incluye features reales no publicadas")
print("por MIROVA (cat-b: lacolito PCC, Lazufre, etc.). En MODIS la baja precisión es")
print("mayormente artefacto de campo difuso (cat-d, S101) — el frente §2.")

# recall MODIS por volcán (dónde concentra)
print("\nMODIS recall por volcán (MIROVA det / TP):")
for vol in VOLS:
    miro = {k for k in mir["MODIS"] if k[0] == vol}
    if not miro:
        continue
    tp = sum(1 for k in miro if k in ours["MODIS"])
    print(f"  {vol:<20} {tp}/{len(miro)}")

json.dump(out, open(Path(__file__).parent / "recall_by_sensor_result.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("\n-> recall_by_sensor_result.json")
