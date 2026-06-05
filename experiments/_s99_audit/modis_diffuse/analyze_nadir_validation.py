"""S101 — Análisis de la validación nadir-fijo MODIS de los 11 vols (run 27022484062).

Decide los 3 ajustes del fix compuesto:
  1) PISO: barrer min_vrp_mw_modis candidatos {0.27,0.15,0.10,0.05} → cuántos
     confirmados MIROVA-MODIS se pierden (FN) y cuánto ruido entra en cada uno.
  2) MAGNITUD vs MIROVA: por vol, ratio nadir vs MIROVA en confirmados (¿clava?).
  3) RESIDUO path D: records altos (>20 MW) con nadir SIN MIROVA = artefacto residual
     (la 2ª palanca). Y filtros display: cuántos quedan visibles (para recalibrar).

Uso:
  gh run download 27022484062 -D experiments/_s99_audit/_nadir_val_art
  python experiments/_s99_audit/modis_diffuse/analyze_nadir_validation.py
Fuente S91: este script. Output stdout + JSON.
"""
import json, csv, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "experiments/_s99_audit/_nadir_val_art"
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica", "Llaima",
        "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria", "NevadosDeChillan"]
namemap = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "NevadosDeChillan": "Nevados de Chillan"}
PISOS = [0.27, 0.15, 0.10, 0.05]


def load(vol):
    f = ART / f"nadir-val-{vol}" / f"{vol}.json"
    if not f.exists():
        return None
    o = json.load(open(f, encoding="utf-8"))
    return [r for r in (o["records"] if isinstance(o, dict) else o) if r.get("sensor", "").startswith("MODIS")]


def pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


# MIROVA MODIS confirmados (vol, dia)
mir = defaultdict(set)
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA":
        mir[r["Volcan"]].add(r["Fecha_Satelite_UTC"][:10])

allrec = {}
for vol in VOLS:
    rs = load(vol)
    if rs is None:
        print(f"FALTA artifact: {vol}")
    else:
        allrec[vol] = rs

# 1) PISO: FN vs ruido por candidato
print("=== 1) Elección de piso (FN confirmados perdidos / records totales sobre piso) ===")
print(f"{'piso':>6} | " + " ".join(f"{v[:5]:>6}" for v in VOLS) + " | totFN  totRec")
for piso in PISOS:
    fns, recs = [], 0
    row_fn = []
    for vol in VOLS:
        rs = allrec.get(vol, [])
        mname = namemap.get(vol, vol)
        conf_days = mir.get(mname, set())
        fn = sum(1 for r in rs if str(r.get("datetime_utc", ""))[:10] in conf_days and 0 < pc(r) < piso)
        nrec = sum(1 for r in rs if pc(r) >= piso)
        row_fn.append(fn); recs += nrec
    print(f"{piso:>6} | " + " ".join(f"{x:>6}" for x in row_fn) + f" | {sum(row_fn):>5}  {recs:>6}")

# 2) magnitud vs MIROVA en confirmados
print("\n=== 2) Magnitud nadir vs MIROVA-MODIS (confirmados, ratio mediana) ===")
mir_vrp = defaultdict(dict)
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA":
        try:
            mir_vrp[r["Volcan"]][r["Fecha_Satelite_UTC"][:10]] = float(r["VRP_MW"])
        except ValueError:
            pass
for vol in VOLS:
    rs = allrec.get(vol, [])
    mname = namemap.get(vol, vol)
    ratios = []
    for r in rs:
        day = str(r.get("datetime_utc", ""))[:10]
        if day in mir_vrp.get(mname, {}) and pc(r) > 0 and mir_vrp[mname][day] > 0:
            ratios.append(pc(r) / mir_vrp[mname][day])
    if ratios:
        print(f"  {vol:<20} ratio mediana={statistics.median(ratios):.2f} (n={len(ratios)})")

# 3) residuo path D (artefacto >20 MW sin MIROVA) + magnitud máxima por vol
print("\n=== 3) Residuo path D con nadir (records >20 MW sin MIROVA = artefacto) ===")
out = {}
for vol in VOLS:
    rs = allrec.get(vol, [])
    mname = namemap.get(vol, vol)
    conf_days = mir.get(mname, set())
    resid = [(str(r.get("datetime_utc", ""))[:10], round(pc(r))) for r in rs
             if pc(r) > 20 and str(r.get("datetime_utc", ""))[:10] not in conf_days]
    maxv = max((pc(r) for r in rs), default=0)
    print(f"  {vol:<20} residuo>20MW={len(resid)}  max={maxv:.0f} MW  {sorted(resid, key=lambda x:-x[1])[:3]}")
    out[vol] = {"residuo_gt20": len(resid), "max_mw": round(maxv, 1)}

json.dump(out, open(Path(__file__).parent / "analyze_nadir_validation_result.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("\n-> analyze_nadir_validation_result.json")
print("Lectura: elegir el piso con FN=0 (o mínimo) y menos ruido. Si queda residuo path D")
print("alto en PCC/Tupun, ese es el frente de la 2ª palanca.")
