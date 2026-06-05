"""S101 — Auditoría conservadora pre-nadir-fijo MODIS (riesgos antes de A45).

1) Validez del A/B: ¿el brazo OFF (sec³ reproc) reproduce el operacional actual?
   (si difiere mucho, el A/B tiene confounder de granules).
2) FN check: de los records MODIS que MIROVA confirma (Láscar+singletons), ¿cuántos
   caen bajo el piso min_vrp_mw_modis=0.27 con nadir-fijo? (riesgo de perder detección).
3) Filtros display: ¿cuántos records que HOY oculta isDiffuseFieldArtifact (≥50 MW) o
   isCirrusArtifact (>10 MW) caen bajo el umbral con nadir-fijo (reaparecen)?

Fuente S91: este script. Output stdout + JSON.
"""
import json, csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "experiments/_s99_audit/_sec3_art"
VOLS = ["PuyehueCordonCaulle", "Tupungatito", "Lascar"]
namemap = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
PISO = 0.27
CIRRUS_VRP = 10.0
DIFFUSE_VRP = 50.0


def load(prof, vol):
    f = ART / f"sec3-{prof}-{vol}" / f"{vol}.json"
    if not f.exists():
        return None
    o = json.load(open(f, encoding="utf-8"))
    return {(r.get("datetime_utc"), r.get("sensor")): r
            for r in (o["records"] if isinstance(o, dict) else o) if r.get("sensor", "").startswith("MODIS")}


def load_op(vol):
    f = REPO / "data/mirova_equivalent" / f"{vol}.json"
    o = json.load(open(f, encoding="utf-8"))
    return {(r.get("datetime_utc"), r.get("sensor")): r
            for r in (o["records"] if isinstance(o, dict) else o) if r.get("sensor", "").startswith("MODIS")}


def pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


def tmax(r):
    # t_max del cluster para los filtros display
    return r.get("t_max_k") or r.get("diag_t_max_k") or 0


# MIROVA MODIS confirmados
mir = defaultdict(set)
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA":
        mir[r["Volcan"]].add(r["Fecha_Satelite_UTC"][:10])

out = {}
print("=== 1) Validez A/B: brazo OFF (sec³ reproc) vs operacional (abril, records comunes) ===")
for vol in VOLS:
    off, op = load("_sec3_modis_nadir_off", vol), load_op(vol)
    if not off:
        print(f"  {vol}: sin artifact"); continue
    common = [k for k in off if k in op and "2026-04" in str(k[0])]
    diffs = [abs(pc(off[k]) - pc(op[k])) for k in common if pc(op[k]) > 0]
    near = sum(1 for k in common if pc(op[k]) > 0 and abs(pc(off[k]) - pc(op[k])) < 0.01 * max(pc(op[k]), 1))
    print(f"  {vol}: {len(common)} comunes abril; |off-op|<1% en {near}/{sum(1 for k in common if pc(op[k])>0)} (resto = drift granule)")

print(f"\n=== 2) FN check: MIROVA-confirmados que caen bajo piso {PISO} MW con nadir ===")
for vol in VOLS:
    on = load("_sec3_modis_nadir_on", vol)
    if not on:
        continue
    mname = namemap.get(vol, vol)
    conf = [k for k in on if str(k[0])[:10] in mir.get(mname, set())]
    under = [(k[0], round(pc(on[k]), 3)) for k in conf if 0 < pc(on[k]) < PISO]
    print(f"  {vol}: {len(conf)} confirmados en abril; bajo piso con nadir: {len(under)} {under[:4]}")

print(f"\n=== 3) Filtros display: artefactos que HOY oculta y REAPARECEN con nadir ===")
for vol in VOLS:
    off, on = load("_sec3_modis_nadir_off", vol), load("_sec3_modis_nadir_on", vol)
    if not off or not on:
        continue
    reaparece_dif, reaparece_cir = [], []
    for k in set(off) & set(on):
        vo, vn = pc(off[k]), pc(on[k])
        tm = tmax(off[k])
        # isDiffuseFieldArtifact (aprox): t_max<278.15 ∧ vrp>=50 (hoy oculto) -> nadir <50 (reaparece)
        if tm and tm < 278.15 and vo >= DIFFUSE_VRP and vn < DIFFUSE_VRP:
            reaparece_dif.append((str(k[0])[:10], round(vo), round(vn)))
        # isCirrusArtifact: t_max<273.15 ∧ vrp>10 (hoy oculto) -> nadir <10 (reaparece)
        if tm and tm < 273.15 and vo > CIRRUS_VRP and vn <= CIRRUS_VRP:
            reaparece_cir.append((str(k[0])[:10], round(vo), round(vn)))
    print(f"  {vol}: difuso reaparece={len(reaparece_dif)} {reaparece_dif[:3]} | cirrus reaparece={len(reaparece_cir)} {reaparece_cir[:3]}")
    out[vol] = {"diffuse_reaparece": len(reaparece_dif), "cirrus_reaparece": len(reaparece_cir)}

json.dump(out, open(Path(__file__).parent / "audit_nadir_safety_result.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("\n-> audit_nadir_safety_result.json")
