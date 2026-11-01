# -*- coding: utf-8 -*-
"""V4 / 282: conteo independiente por la bandera primary_cluster.d9_capped (no por igualdad a 5,0) y pc.vrp_mw > 5,
por régimen (K = regimen.codigo_sha presente). Control positivo: el corpus de 88e97d84e (2026-10-14), donde la marca
S151 dice 1.565 con d9_capped; si la bandera se leyera mal, ahí daría 0."""
import json, sys, glob, os, collections
for raiz in sys.argv[1:]:
    c = collections.Counter(); chillan = collections.Counter()
    for f in sorted(glob.glob(os.path.join(raiz, "*.json"))):
        v = os.path.basename(f)[:-5]
        for r in json.load(open(f, encoding="utf-8")).get("records", []):
            pc = r.get("primary_cluster") or {}
            k = "K" if (r.get("regimen") or {}).get("codigo_sha") else "C0"
            c[("n", k)] += 1
            if pc.get("d9_capped"): c[("capped", k)] += 1
            pv = pc.get("vrp_mw")
            if isinstance(pv, (int, float)) and pv > 5.0 + 1e-9: c[("sobre5", k)] += 1
            if v == "NevadosDeChillan" and r.get("datetime_utc", "") >= "2026-09-01":
                chillan["n"] += 1
                if pc.get("d9_capped"): chillan["capped"] += 1
                if isinstance(pv, (int, float)) and pv > 5.0 + 1e-9: chillan["sobre5"] += 1
    print(raiz); print("  ", dict(sorted(c.items()))); print("   Chillan desde 2026-09-01:", dict(chillan))
