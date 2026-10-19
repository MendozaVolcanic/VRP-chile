"""F3: campos del Test 1 y del ancla que cambian de sentido con K, por régimen (C0 < 2026-09-18 <= K),
ventana 2026-08-20..2026-10-19, 11 Tier A. P1: si K no hubiera apagado el Test 1, triggered_test1 seguiría
> 0 en K. P2: n por estrato impreso; un campo ausente se cuenta como 'ausente', no como False."""
import json, os, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VOLS = ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]
c = defaultdict(Counter)
for v in VOLS:
    for r in json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        d = r["datetime_utc"][:10]
        if not ("2026-08-20" <= d <= "2026-10-19"): continue
        reg = "C0" if d < "2026-09-18" else "K"
        c[reg]["n"] += 1
        t = r.get("triggered_test1")
        c[reg]["triggered_test1=" + ("ausente" if t is None else str(t))] += 1
        c[reg]["fh_source=" + str(r.get("final_hotspot_source"))] += 1
        c[reg]["n_test1_pixels>0"] += int((r.get("n_test1_pixels") or 0) > 0)
        c[reg]["f5_core_presente"] += int(isinstance(r.get("f5_core_vrp_mw"), (int, float)))
        c[reg]["pc_presente"] += int(bool(r.get("primary_cluster")))
for reg in ("C0","K"):
    print(reg, dict(sorted(c[reg].items())))
