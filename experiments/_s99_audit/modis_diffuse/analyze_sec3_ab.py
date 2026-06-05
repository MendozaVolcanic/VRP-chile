"""S101 — Análisis del A/B palanca sec³ MODIS (run 27012025326).

Compara por record COMÚN (dt+sensor) la magnitud pc.vrp_mw entre:
  off = _sec3_modis_nadir_off (sec³ activo, operacional)
  on  = _sec3_modis_nadir_on  (nadir-fijo, como MIROVA resamplea)
Ratio off/on = factor de inflación sec³ puro (geometría de escaneo off-nadir).
Cruza el brazo ON contra MIROVA-MODIS (¿nadir-fijo acerca a MIROVA?).

Uso:
  gh run download 27012025326 -D experiments/_s99_audit/_sec3_art
  python experiments/_s99_audit/modis_diffuse/analyze_sec3_ab.py
Fuente S91: este script. Output stdout + JSON.
"""
import json, csv, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "experiments/_s99_audit/_sec3_art"
VOLS = ["PuyehueCordonCaulle", "Tupungatito", "Lascar"]
namemap = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _load(profile, vol):
    for cand in [ART / f"sec3-{profile}-{vol}" / f"{vol}.json",
                 *ART.rglob(f"sec3-{profile}-{vol}/{vol}.json")]:
        if cand.exists():
            return {(r.get("datetime_utc"), r.get("sensor")): r for r in _recs(json.load(open(cand, encoding="utf-8")))
                    if r.get("sensor", "").startswith("MODIS")}
    return None


# MIROVA MODIS por (vol,dia)
mir = defaultdict(list)
for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
    if r["Sensor"] == "MODIS" and r["Tipo_Registro"] == "ALERTA_TERMICA":
        try:
            mir[(r["Volcan"], r["Fecha_Satelite_UTC"][:10])].append(float(r["VRP_MW"]))
        except ValueError:
            pass


def pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


out = {}
print("=== A/B palanca sec³ MODIS — ratio off(sec³)/on(nadir) por record común ===\n")
for vol in VOLS:
    off, on = _load("_sec3_modis_nadir_off", vol), _load("_sec3_modis_nadir_on", vol)
    if off is None or on is None:
        print(f"{vol}: FALTA artifact (off={off is not None} on={on is not None})")
        continue
    common = set(off) & set(on)
    ratios, on_vals, off_vals = [], [], []
    big_ratios = []  # ratio en records inflados (off>20)
    for k in common:
        vo, vn = pc(off[k]), pc(on[k])
        if vo > 0 and vn > 0:
            ratios.append(vo / vn); off_vals.append(vo); on_vals.append(vn)
            if vo > 20:
                big_ratios.append(vo / vn)
    mname = namemap.get(vol, vol)
    # nadir-on vs MIROVA en records con MIROVA
    on_vs_mir = []
    for k in on:
        day = str(k[0])[:10]
        if (mname, day) in mir and pc(on[k]) > 0:
            on_vs_mir.append(pc(on[k]) / max(mir[(mname, day)]))
    def md(x):
        return round(statistics.median(x), 2) if x else None
    print(f"{vol}: comunes={len(common)}  records con pc>0 ambos={len(ratios)}")
    print(f"   ratio sec³ (off/on) mediana={md(ratios)}  max={round(max(ratios),2) if ratios else None}")
    print(f"   en inflados off>20MW: ratio sec³ mediana={md(big_ratios)} (n={len(big_ratios)})")
    print(f"   magnitud off mediana={md(off_vals)} MW  ->  on(nadir) mediana={md(on_vals)} MW")
    if on_vs_mir:
        print(f"   nadir-on vs MIROVA-MODIS: ratio mediana={md(on_vs_mir)} (n={len(on_vs_mir)})")
    print()
    out[vol] = {"n_common": len(common), "ratio_sec3_med": md(ratios),
                "ratio_sec3_big_med": md(big_ratios), "off_med": md(off_vals),
                "on_med": md(on_vals), "on_vs_mir_med": md(on_vs_mir) if on_vs_mir else None}

json.dump(out, open(Path(__file__).parent / "analyze_sec3_ab_result.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("-> analyze_sec3_ab_result.json")
print("\nLectura: ratio sec³ ~1 = sec³ NO infla (palanca chica); ratio >2 = sec³ infla fuerte")
print("(la palanca es la magnitud). Si nadir-on sigue >>MIROVA, el resto es path D (detección).")
