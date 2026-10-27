"""S165, issue #915: cúmulos topados por D9 (5 MW, primary_cluster.d9_capped) en la ventana del audit (2026-08-27 a
2026-10-26), en los tres volcanes del issue. Solo lectura sobre el árbol de origin/main extraído (sha en SHA.txt)."""
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "D:/vrp-trabajo/temporales/s165_issue915/main"
print("sha main:", open(os.path.join(ROOT, "SHA.txt")).read().strip())
for v in ["NevadosDeChillan", "PuyehueCordonCaulle", "Tupungatito"]:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))
    c = [(r["datetime_utc"], r["sensor"], r["primary_cluster"].get("vrp_mw"), r.get("distance_class"))
         for r in d["records"] if "2026-08-27" <= r["datetime_utc"][:10] <= "2026-10-26"
         and (r.get("primary_cluster") or {}).get("d9_capped")]
    print(v, len(c), c)
