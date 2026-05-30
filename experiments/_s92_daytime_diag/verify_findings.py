"""S92 §0.5 — verifica que las afirmaciones de FINDINGS.md coinciden con los datos.
Imprime OK/MISMATCH por afirmación y ALL_VERIFIED solo si todo cuadra.
"""
import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.process_modis import _parse_datetime, _scene_is_day  # noqa: E402

NDC_LAT, NDC_LON = -36.86483, -71.38068  # mirova_center NdC (impreso por diag.py)
ok = True


def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK ' if cond else 'MISMATCH'}] {name} {detail}")


def load(p):
    return json.load(open(p, encoding="utf-8"))["records"]


def is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


# ---- #2.1: NdC MODIS día/noche ----
print("#2.1 — NdC MODIS día/noche")
recs = load(ROOT / "data/_daytime_modis_disabled/NevadosDeChillan.json")
modis_ab = [r for r in recs if is_modis(r)
            and "2026-03-01" <= str(r.get("datetime_utc", "")) <= "2026-04-30 23:59"]
day = night = unparsed = 0
hours = Counter()
for r in modis_ab:
    g = r.get("granule", "")
    iso = _parse_datetime(g)
    if iso == "unknown":
        unparsed += 1
        continue
    hours[iso[11:13]] += 1
    if _scene_is_day(g, NDC_LAT, NDC_LON):
        day += 1
    else:
        night += 1
check("MODIS en rango AB == 135", len(modis_ab) == 135, f"(={len(modis_ab)})")
check("day == 0", day == 0, f"(={day})")
check("night == 135", night == 135, f"(={night})")
check("unparsed == 0", unparsed == 0, f"(={unparsed})")
check("ninguna hora UTC en rango diurno 13-17", not any(13 <= int(h) <= 17 for h in hours),
      f"(horas={dict(sorted(hours.items()))})")
ev = [r for r in modis_ab if str(r.get("datetime_utc", "")).startswith("2026-03-17")]
check("2026-03-17 tiene 2 records", len(ev) == 2, f"(={len(ev)})")
check("ambos del 03-17 son noche",
      all(not _scene_is_day(r.get("granule", ""), NDC_LAT, NDC_LON) for r in ev))

# ---- #2.2: ningún campo de record difiere enabled vs disabled ----
print("#2.2 — enabled vs disabled (no fuga VIIRS)")


def key(r):
    return r.get("granule") or (r.get("datetime_utc"), r.get("sensor"))


def loadfull(p):
    return json.load(open(p, encoding="utf-8"))


for vol, n_expected in [("Villarrica", 342), ("NevadosDeChillan", 657)]:
    fe = loadfull(ROOT / f"data/_daytime_modis_enabled/{vol}.json")
    fd = loadfull(ROOT / f"data/_daytime_modis_disabled/{vol}.json")
    en = {key(r): r for r in fe["records"]}
    di = {key(r): r for r in fd["records"]}
    common = set(en) & set(di)
    n_field_diffs = 0
    for k in common:
        re_, rd = en[k], di[k]
        for f in set(re_) | set(rd):
            a, b = re_.get(f), rd.get(f)
            if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
                n_field_diffs += 1
    check(f"{vol}: records == {n_expected}", len(common) == n_expected, f"(={len(common)})")
    check(f"{vol}: 0 campos de record difieren", n_field_diffs == 0, f"(={n_field_diffs})")
    check(f"{vol}: solo 'updated' top-level difiere",
          fe.get("updated") != fd.get("updated"))

print()
print("ALL_VERIFIED" if ok else "VERIFICATION_FAILED")
sys.exit(0 if ok else 1)
