"""Para las 5 sin publicar: ¿otra pasada nocturna del mismo volcan y fecha UTC se publico? (harness propio)."""
import json, os, subprocess, sys, math
from datetime import datetime, timezone
W = sys.argv[1]
INNER = {"Tupungatito": 7, "PuyehueCordonCaulle": 20, "NevadosDeChillan": 5}
casos5 = [("Tupungatito", "2026-09-28", "2026-09-28 05:18"), ("Tupungatito", "2026-09-29", "2026-09-29 04:54"),
          ("PuyehueCordonCaulle", "2026-10-10", "2026-10-10 05:54"), ("NevadosDeChillan", "2026-10-12", "2026-10-12 07:20"),
          ("NevadosDeChillan", "2026-10-15", "2026-10-15 01:05")]
casos, meta = [], []
for vol, fecha, excl in casos5:
    for r in json.load(open(os.path.join(W, "data/mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]:
        if r["datetime_utc"][:10] == fecha and r["datetime_utc"][:16] != excl:
            casos.append([r, INNER[vol]]); meta.append((vol, fecha, r["datetime_utc"], r["sensor"]))
json.dump(casos, open("_c5.json", "w", encoding="utf-8"))
o = subprocess.run(["node", "pred.js", os.path.join(W, "frontend/index.html"), "_c5.json"], capture_output=True, text=True, encoding="utf-8")
p = json.loads(o.stdout); os.remove("_c5.json")
for vol, fecha, excl in casos5:
    pubs = [(m[2], m[3]) for m, q in zip(meta, p) if m[0] == vol and m[1] == fecha and q["pub"]]
    print(vol, fecha, "otras pasadas publicadas:", pubs)
