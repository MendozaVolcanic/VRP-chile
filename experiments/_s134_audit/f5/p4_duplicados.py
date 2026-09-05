"""P4 - duplicados de records por granule/timestamp.
1) sobre ~/ab_area (los 24 dirs bajados del A/B S133)
2) sobre los 11 Tier A de data/mirova_equivalent/ (raiz canonica, solo lectura)
"""
import io, json, os, glob
from collections import defaultdict

AB_ROOT = os.path.expanduser("~/ab_area")
CANON = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent"
TIER_A = ["Villarrica","Lascar","Isluga","NevadosDeChillan","Llaima","Lastarria",
          "PlanchonPeteroa","Tupungatito","Copahue","PuyehueCordonCaulle","Chaiten"]

def cuenta_dup(path, key_fields=("granule",)):
    with io.open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    recs = doc["records"] if isinstance(doc, dict) else doc
    vistos = defaultdict(int)
    for r in recs:
        key = tuple(r.get(f) for f in key_fields)
        if key == (None,) * len(key_fields):
            continue
        vistos[key] += 1
    dup = {k: c for k, c in vistos.items() if c > 1}
    return len(recs), len(dup), sum(c - 1 for c in dup.values())

print("=== 1) ~/ab_area (24 dirs) ===")
if os.path.isdir(AB_ROOT):
    dirs = sorted(os.listdir(AB_ROOT))
    print(f"dirs encontrados: {len(dirs)}")
    tot_recs = tot_dupkeys = tot_extra = 0
    for d in dirs:
        for jf in glob.glob(os.path.join(AB_ROOT, d, "*.json")):
            n, ndup, extra = cuenta_dup(jf, ("granule",))
            tot_recs += n; tot_dupkeys += ndup; tot_extra += extra
            if ndup:
                print(f"  {d}/{os.path.basename(jf)}: n={n} granule_dup_keys={ndup} extra_recs={extra}")
    print(f"TOTAL ab_area: n_records={tot_recs} granule_dup_keys={tot_dupkeys} extra_recs={tot_extra}")
else:
    print("NO EXISTE ~/ab_area")

print()
print("=== 2) 11 Tier A canonicos, key=(sensor,granule) y (sensor,datetime_utc) ===")
if os.path.isdir(CANON):
    for vol in TIER_A:
        path = os.path.join(CANON, vol + ".json")
        if not os.path.exists(path):
            print(f"  {vol}: NO EXISTE {path}")
            continue
        n1, ndup1, extra1 = cuenta_dup(path, ("sensor", "granule"))
        n2, ndup2, extra2 = cuenta_dup(path, ("sensor", "datetime_utc"))
        print(f"  {vol}: n={n1} dup(sensor,granule)={ndup1}/{extra1}  dup(sensor,datetime_utc)={ndup2}/{extra2}")
else:
    print("NO EXISTE ruta canonica", CANON)
