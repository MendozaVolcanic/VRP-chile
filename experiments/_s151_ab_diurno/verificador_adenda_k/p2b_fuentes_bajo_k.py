# Verificador adenda K: en los records de produccion escritos con K (regimen con codigo_sha posterior al merge de #850,
# o processed_utc >= 2026-10-18 09:57:30 UTC), que final_hotspot_source y triggered_test1 aparecen. Si test1_roi no
# aparece nunca bajo K, sirve de invariante a nivel de record para el cableado del A/B.
import collections, json, sys
from pathlib import Path
d = Path(sys.argv[1])
corte = "2026-10-18T09:57:30"
src = collections.Counter(); t1 = collections.Counter(); n = 0; shas = collections.Counter()
for f in sorted(d.glob("*.json")):
    for r in json.load(open(f, encoding="utf-8")).get("records", []):
        pu = str(r.get("processed_utc") or "")
        if pu.replace(" ", "T") < corte:
            continue
        n += 1
        src[r.get("final_hotspot_source")] += 1
        t1[r.get("triggered_test1")] += 1
        shas[(r.get("regimen") or {}).get("codigo_sha", "")[:9]] += 1
print("records procesados desde", corte, ":", n)
print("final_hotspot_source:", dict(src))
print("triggered_test1:", dict(t1))
print("codigo_sha:", dict(shas))
