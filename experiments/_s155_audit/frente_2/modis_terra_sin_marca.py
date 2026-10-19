"""Records posteriores al 2026-09-18 sin regimen.codigo_sha: cuales son, cuando se procesaron y si publican.
Pregunta 1: si hubiera records C0 sueltos dentro de la ventana K, este listado los muestra uno por uno.
Pregunta 2: si el campo regimen no existiera en ninguno, la lista seria de todos los records (no 26): se imprime el total.
Denominador: records de data/mirova_equivalent/<11 Tier A>.json con datetime_utc >= 2026-09-18."""
import json, glob, os, io, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
tot = 0; sin = []
for f in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    for r in d["records"]:
        if (r.get("datetime_utc") or "") < "2026-09-18": continue
        tot += 1
        if not (r.get("regimen") or {}).get("codigo_sha"):
            pc = r.get("primary_cluster") or {}
            sin.append((d["volcano"], r["datetime_utc"], r["sensor"], r.get("processed_utc"), r.get("first_processed_utc"), r.get("product_version"), r.get("triggered_test1"), r.get("distance_class"), pc.get("vrp_mw"), r.get("granule")))
print("records >= 2026-09-18:", tot, " sin marca:", len(sin))
for s in sin: print("  ", s)
print(collections.Counter(s[1][:10] for s in sin))

# Segunda parte: hay un record K del mismo sensor dentro de +-10 min (duplicado) y que se publicaria en PCC.
from datetime import datetime
def t(s): return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
for vol, dt, sen, *_ in sin:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))
    vecinos = [r for r in d["records"] if r["sensor"] == sen and abs((t(r["datetime_utc"]) - t(dt)).total_seconds()) <= 600 and (r.get("regimen") or {}).get("codigo_sha")]
    if vecinos: print("DUPLICADO K:", vol, dt, sen, [v["datetime_utc"] for v in vecinos])
d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", "PuyehueCordonCaulle.json"), encoding="utf-8"))
for r in d["records"]:
    if r["sensor"] == "MODIS_TERRA" and r["datetime_utc"] in ("2026-09-28 01:25", "2026-10-10 01:05"):
        pc = r.get("primary_cluster") or {}
        print("PCC", r["datetime_utc"], "dc", r.get("distance_class"), "pc_dist", pc.get("centroid_dist_km"), "pc_vrp", pc.get("vrp_mw"), "src", r.get("final_hotspot_source"), "regimen", r.get("regimen"))
