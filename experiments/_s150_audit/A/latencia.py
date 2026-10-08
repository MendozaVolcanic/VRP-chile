"""S150 frente A: latencia NRT = processed_utc - datetime_utc, por sensor y producto.
Ventana: pasadas con datetime_utc entre 2026-09-08 y 2026-10-02 (antes del apagon), 11 Tier A.
P1: si el NRT se atrasara, la mediana crece (lo ve). Sesgo conocido (store.py:488-499 + 623-624):
processed_utc se reescribe al promover NRT->standard, asi que en records 'standard' mide la
promocion, no la primera publicacion; por eso se separa por product_version.
P2: records sin processed_utc se cuentan aparte (SIN DATO), no como latencia cero."""
import json, sys, glob, statistics, collections
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")
g = collections.defaultdict(list); sin = collections.Counter()
for p in glob.glob("data/mirova_equivalent/*.json"):
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc", "")
        if not ("2026-09-08" <= dt[:10] <= "2026-10-02"): continue
        if not r.get("processed_utc"): sin[r.get("sensor")] += 1; continue
        a = datetime.strptime(dt, "%Y-%m-%d %H:%M"); b = datetime.strptime(r["processed_utc"], "%Y-%m-%dT%H:%M:%SZ")
        s = r.get("sensor", ""); fam = "MODIS" if "MODIS" in s or s in ("Terra","Aqua") else ("V750" if s.endswith("_750") else "V375")
        g[(fam, r.get("product_version"))].append((b - a).total_seconds() / 3600)
for k in sorted(g, key=str):
    v = sorted(g[k]); q = lambda f: v[min(len(v)-1, int(f*len(v)))]
    print(f"{k[0]:5s} {str(k[1]):9s} n={len(v):5d} p10={q(.1):6.1f} h mediana={q(.5):6.1f} h p90={q(.9):6.1f} h")
print("sin processed_utc:", dict(sin))
