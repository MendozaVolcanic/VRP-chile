# -*- coding: utf-8 -*-
import json, sys, io
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[5]  # raiz del repo
DESDE, HASTA = "2025-02-15", "2026-09-17"
vols = sys.argv[1:]
for v in vols:
    op = json.load(open(RAIZ / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))["records"]
    re_ = json.load(open(RAIZ / "data/_s154_reproc_k_historico" / f"{v}.json", encoding="utf-8"))["records"]
    sinmarca_fuera = [(r["datetime_utc"], r["sensor"], r.get("product_version"), r.get("processed_utc")) for r in op
                      if r["datetime_utc"][:10] > HASTA and not (r.get("regimen") or {}).get("perfil")]
    conmarca_dentro = [(r["datetime_utc"], r["sensor"]) for r in op
                       if r["datetime_utc"][:10] <= HASTA and (r.get("regimen") or {}).get("perfil")]
    k_min = min((r["datetime_utc"] for r in op if (r.get("regimen") or {}).get("perfil")), default=None)
    none_max = max((r["datetime_utc"] for r in op if not (r.get("regimen") or {}).get("perfil") and r["datetime_utc"][:10] <= HASTA), default=None)
    print(f"== {v}: primer K {k_min} | ultimo sin marca en ventana {none_max}")
    print("   sin marca fuera de ventana:", sinmarca_fuera)
    print("   con marca dentro de ventana:", len(conmarca_dentro), conmarca_dentro[:3])

    def stats(recs, tag):
        by = defaultdict(lambda: Counter())
        for r in recs:
            s = r.get("sensor")
            c = by[s]
            c["n"] += 1
            c["ap"] += len(r.get("anomaly_pixels") or [])
            c["f5"] += "f5_core_vrp_mw" in r
            c["disc"] += "discarded_reason" in r
            c["pub"] += (r.get("distance_class") == "summit" and (r.get("vrp_mw") or 0) > 0)
            c["pc"] += bool(r.get("primary_cluster"))
            c["sza"] += "solar_zenith_deg" in r
        print(f"   {tag}:")
        for s in sorted(by):
            c = by[s]
            print(f"     {s:18s} n={c['n']:5d} ap/rec={c['ap']/c['n']:.2f} f5={c['f5']/c['n']:.2f} disc={c['disc']/c['n']:.2f} pub={c['pub']/c['n']:.3f} pc={c['pc']/c['n']:.2f} sza={c['sza']/c['n']:.2f}")
    post = [r for r in op if r["datetime_utc"][:10] > HASTA and (r.get("regimen") or {}).get("perfil") == "mirova_equivalent"]
    stats(post, "op con K (post ventana)")
    stats([r for r in re_ if "2026-08-15" <= r["datetime_utc"][:10] <= HASTA], "reproceso 2026-08-15..09-17")
    stats([r for r in op if "2026-08-15" <= r["datetime_utc"][:10] <= HASTA], "op viejo 2026-08-15..09-17")
