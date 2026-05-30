"""S92 — cierre #2.2: el md5 enabled vs disabled difiere pese a vrp_mw/pc idénticos.
¿QUÉ campo difiere exactamente? Deep diff por record emparejado por granule.

Si lo único que cambia es `updated` (top-level) y/o el ORDEN de records, la
diferencia de md5 es benigna (timestamps de reproc distintos). Si difiere algún
campo de detección en VIIRS -> hay que mirarlo.
"""
import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]


def loadfull(p):
    return json.load(open(p, encoding="utf-8"))


def key(r):
    return r.get("granule") or (r.get("datetime_utc"), r.get("sensor"))


def sensor_bucket(s):
    s = str(s)
    return "MODIS" if s.startswith("MODIS") else ("VIIRS" if s.startswith("VIIRS") else "OTHER")


def deep_ne(a, b):
    # compara con tolerancia para floats; estructuras se serializan canónicamente
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) > 1e-9
        except (TypeError, ValueError):
            return a != b
    if isinstance(a, dict) and isinstance(b, dict):
        return json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True)
    if isinstance(a, list) and isinstance(b, list):
        return json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True)
    return a != b


def analyze(vol):
    fe = loadfull(ROOT / f"data/_daytime_modis_enabled/{vol}.json")
    fd = loadfull(ROOT / f"data/_daytime_modis_disabled/{vol}.json")
    print(f"\n===== {vol} =====")
    print(f"top-level 'updated' enabled={fe.get('updated')!r} disabled={fd.get('updated')!r} "
          f"-> {'DIFIERE' if fe.get('updated')!=fd.get('updated') else 'igual'}")
    en = {key(r): r for r in fe["records"]}
    di = {key(r): r for r in fd["records"]}
    # orden idéntico?
    order_en = [key(r) for r in fe["records"]]
    order_di = [key(r) for r in fd["records"]]
    print(f"orden de records identico: {order_en == order_di}")

    field_diff = Counter()           # campo -> nº records que difieren (cualquier sensor)
    field_diff_viirs = Counter()     # campo -> nº records VIIRS que difieren
    recs_with_any_diff = Counter()   # sensor -> nº records con >=1 campo distinto
    for k in (set(en) & set(di)):
        re_, rd = en[k], di[k]
        sb = sensor_bucket(re_.get("sensor"))
        allk = set(re_) | set(rd)
        rec_has = False
        for f in allk:
            if deep_ne(re_.get(f), rd.get(f)):
                field_diff[f] += 1
                if sb == "VIIRS":
                    field_diff_viirs[f] += 1
                rec_has = True
        if rec_has:
            recs_with_any_diff[sb] += 1

    print(f"records con >=1 campo distinto, por sensor: {dict(recs_with_any_diff)}")
    print(f"campos que difieren (cualquier sensor) -> nº records:")
    for f, n in field_diff.most_common():
        print(f"    {f}: {n}  (VIIRS: {field_diff_viirs.get(f,0)})")
    if not field_diff:
        print("    NINGUN campo de record difiere (solo cambia 'updated'/orden).")


if __name__ == "__main__":
    for vol in ["Villarrica", "NevadosDeChillan"]:
        analyze(vol)
