"""S92 — Diagnóstico bug #2.2: ¿el flag enable_daytime_modis altera records VIIRS?

Reproducible. Fuente de verdad de los números del FINDINGS S92 (regla §0.5).

Empareja records enabled vs disabled por (granule) y compara:
  - vrp_mw           (scene-wide)  -> si difiere en VIIRS = fuga de scope (BUG real)
  - primary_cluster.vrp_mw (=mirova_eq_vrp) -> si solo esto difiere con vrp_mw
    igual = cluster selection no determinista del reproc (ruido A18, NO bug)

El código (store._reject_daytime + process_viirs sin flag) predice que el flag
NO toca VIIRS. Este script lo confirma/refuta con los datos del A/B.
"""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]


def load(p):
    return json.load(open(p, encoding="utf-8"))["records"]


def pc_vrp(r):
    pc = r.get("primary_cluster")
    if isinstance(pc, dict):
        return pc.get("vrp_mw")
    return None


def sensor_bucket(s):
    s = str(s)
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS"
    return "OTHER"


def key(r):
    # granule es único por pasada; fallback a (datetime_utc, sensor)
    return r.get("granule") or (r.get("datetime_utc"), r.get("sensor"))


def approx_eq(a, b, tol=1e-6):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol


def analyze(vol):
    en = {key(r): r for r in load(ROOT / f"data/_daytime_modis_enabled/{vol}.json")}
    di = {key(r): r for r in load(ROOT / f"data/_daytime_modis_disabled/{vol}.json")}
    common = set(en) & set(di)
    only_en = set(en) - set(di)
    only_di = set(di) - set(en)
    print(f"\n===== {vol} =====")
    print(f"records enabled={len(en)} disabled={len(di)} | common={len(common)} "
          f"only_enabled={len(only_en)} only_disabled={len(only_di)}")

    diff_vrpmw = Counter()        # por sensor: vrp_mw scene-wide difiere
    diff_pc = Counter()           # por sensor: primary_cluster.vrp_mw difiere
    diff_pc_but_vrpmw_same = Counter()  # ruido cluster A18
    n_common_by_sensor = Counter()
    examples = defaultdict(list)

    for k in common:
        re_, rd = en[k], di[k]
        sb = sensor_bucket(re_.get("sensor"))
        n_common_by_sensor[sb] += 1
        vrp_same = approx_eq(re_.get("vrp_mw"), rd.get("vrp_mw"))
        pc_same = approx_eq(pc_vrp(re_), pc_vrp(rd))
        if not vrp_same:
            diff_vrpmw[sb] += 1
        if not pc_same:
            diff_pc[sb] += 1
            if vrp_same:
                diff_pc_but_vrpmw_same[sb] += 1
            if len(examples[sb]) < 3:
                examples[sb].append(
                    (re_.get("datetime_utc"), re_.get("sensor"),
                     f"vrp_mw {rd.get('vrp_mw')}->{re_.get('vrp_mw')}",
                     f"pc_vrp {pc_vrp(rd)}->{pc_vrp(re_)}"))

    print(f"common por sensor: {dict(n_common_by_sensor)}")
    print(f"DIFIERE vrp_mw (scene-wide) por sensor: {dict(diff_vrpmw)}  "
          f"<- si VIIRS>0 = posible fuga de scope")
    print(f"DIFIERE primary_cluster.vrp_mw por sensor: {dict(diff_pc)}")
    print(f"  de esos, con vrp_mw IGUAL (=ruido cluster A18): {dict(diff_pc_but_vrpmw_same)}")
    for sb, exs in examples.items():
        print(f"  ejemplos {sb}:")
        for e in exs:
            print(f"    {e}")


if __name__ == "__main__":
    for vol in ["Villarrica", "NevadosDeChillan"]:
        analyze(vol)
