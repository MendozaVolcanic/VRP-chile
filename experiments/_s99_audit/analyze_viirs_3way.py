"""S102 — Análisis 3-way del A/B VIIRS (decide la interacción nadir × ctxpeak).

Compara, SOLO records VIIRS, tres brazos sobre la MISMA ventana:
  base  = operacional actual   (sec³ + ctxpeak)   data/mirova_equivalent
  arm1  = nadir + ctxpeak       _viirs_ab_art       (viirs-nadir-ab-<vol>)
  arm2  = nadir + ctxpeak OFF   _viirs_noctx_art    (viirs-noctx-ab-<vol>)

MODIS igual en los 3 => el contraste aísla (sec³→nadir) y (ctxpeak ON→OFF).

Decisión (design doc 2026-06-06 §5):
  - arm2 ratio ~0.85-1.2 global & 0 FN nuevos vs base  -> nadir + RETIRAR ctxpeak.
  - arm2 >1.4 o FN>0                                    -> mantener ctxpeak, adoptar
                                                          nadir (arm1, 0.76).
  - arm2 <0.7                                           -> otro sesgo; NO adoptar.

Uso:
  gh run download <RUN_ID_arm2> -D experiments/_s99_audit/_viirs_noctx_art
  python experiments/_s99_audit/analyze_viirs_3way.py 2026-04-01 2026-05-31
"""
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART1 = REPO / "experiments/_s99_audit/_viirs_ab_art"      # nadir + ctxpeak
ART2 = REPO / "experiments/_s99_audit/_viirs_noctx_art"   # nadir + ctxpeak OFF
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
        "Llaima", "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria",
        "NevadosDeChillan"]
NAMEMAP = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
           "NevadosDeChillan": "Nevados de Chillan"}
W0 = sys.argv[1] if len(sys.argv) > 1 else "2026-04-01"
W1 = sys.argv[2] if len(sys.argv) > 2 else "2026-05-31"


def our_vbucket(s):
    s = str(s or "")
    if not s.startswith("VIIRS"):
        return None
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


def mir_vbucket(s):
    return {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750"}.get(s)


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


def _in(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def our_daily(path):
    """{bucket: {dia: max pc.vrp}} desde un json."""
    if path is None or not Path(path).exists():
        return None
    d = defaultdict(lambda: defaultdict(float))
    for r in _recs(json.load(open(path, encoding="utf-8"))):
        b = our_vbucket(r.get("sensor"))
        if not b or not _in(r):
            continue
        day = str(r.get("datetime_utc", ""))[:10]
        d[b][day] = max(d[b][day], _pc(r))
    return d


def find(art, prefix, vol):
    p = art / f"{prefix}-{vol}" / f"{vol}.json"
    if p.exists():
        return p
    alt = list(art.rglob(f"{prefix}-{vol}/{vol}.json"))
    return alt[0] if alt else None


def load_mirova():
    m = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
        if r["Tipo_Registro"] != "ALERTA_TERMICA":
            continue
        b = mir_vbucket(r["Sensor"])
        if not b:
            continue
        day = r["Fecha_Satelite_UTC"][:10]
        if W0 <= day <= W1:
            try:
                m[r["Volcan"]][b][day].append(float(r["VRP_MW"]))
            except (ValueError, KeyError):
                pass
    return m


def med(xs):
    return statistics.median(xs) if xs else float("nan")


def main():
    mir = load_mirova()
    glob = {s: {"base": [], "a1": [], "a2": [], "fn1": 0, "fn2": 0} for s in ("VIIRS375", "VIIRS750")}
    print(f"=== A/B VIIRS 3-way (ventana {W0}..{W1}) ===")
    print(f"{'Volcan':<18}{'sensor':<9}{'base':>6}{'n+ctx':>7}{'n-ctx':>7}{'FN1':>4}{'FN2':>4}")
    for vol in VOLS:
        base = our_daily(REPO / "data/mirova_equivalent" / f"{vol}.json")
        a1 = our_daily(find(ART1, "viirs-nadir-ab", vol))
        a2 = our_daily(find(ART2, "viirs-noctx-ab", vol))
        if a1 is None or a2 is None:
            print(f"{vol:<18}(falta arm1 o arm2)")
            continue
        mvol = mir.get(NAMEMAP.get(vol, vol), {})
        for sb in ("VIIRS375", "VIIRS750"):
            mdays = mvol.get(sb, {})
            rb, r1, r2, fn1, fn2 = [], [], [], 0, 0
            for day, vrps in mdays.items():
                mv = max(vrps)
                if mv <= 0:
                    continue
                ob = base.get(sb, {}).get(day, 0)
                o1 = a1.get(sb, {}).get(day, 0)
                o2 = a2.get(sb, {}).get(day, 0)
                if ob > 0:
                    rb.append(ob / mv)
                if o1 > 0:
                    r1.append(o1 / mv)
                if o2 > 0:
                    r2.append(o2 / mv)
                if ob > 0 and o1 == 0:
                    fn1 += 1
                if ob > 0 and o2 == 0:
                    fn2 += 1
            glob[sb]["base"] += rb
            glob[sb]["a1"] += r1
            glob[sb]["a2"] += r2
            glob[sb]["fn1"] += fn1
            glob[sb]["fn2"] += fn2
            if mdays:
                print(f"{vol:<18}{sb:<9}{med(rb):>6.2f}{med(r1):>7.2f}{med(r2):>7.2f}{fn1:>4}{fn2:>4}")
    print("\n=== GLOBAL por sensor (ratio mediana vs MIROVA) ===")
    for sb in ("VIIRS375", "VIIRS750"):
        g = glob[sb]
        print(f"  {sb:<9} base={med(g['base']):.2f}  nadir+ctx={med(g['a1']):.2f}  "
              f"nadir-ctx={med(g['a2']):.2f}  FN(nadir+ctx)={g['fn1']}  FN(nadir-ctx)={g['fn2']}")
    print("\nDecisión §5: arm2(nadir-ctx) ~0.85-1.2 & FN=0 -> nadir + RETIRAR ctxpeak.")
    print("            arm2 >1.4 o FN>0 -> mantener ctxpeak + nadir (arm1).")
    print("            arm2 <0.7 -> otro sesgo, NO adoptar.")


if __name__ == "__main__":
    main()
