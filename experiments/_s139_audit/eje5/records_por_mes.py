"""Records (pasadas nocturnas procesadas que cubren el volcan) por volcan, sensor y mes, 2026-01..09,
en data/mirova_equivalent (produccion). Proxy del numero de granules que un reproceso tendra que bajar.
P1: si la data estuviera vacia o truncada, los meses saldrian en 0 y se ven. P2: un volcan sin archivo sale SIN_DATO.
Limite: un record != un granule descargado (los diurnos se descargan? ver fetch nighttime_only) y no cuenta granules sin ROI.
Control positivo: Villarrica agosto 2026 MODIS debe dar ~70 (S133 lo midio)."""
import json, sys, io, collections, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = pathlib.Path(__file__).resolve().parents[3] / "data" / "mirova_equivalent"
TIER = ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]
def bucket(s):
    s = s or ""
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "V750"
    if s.startswith("VIIRS"): return "V375"
    return "?"+s
tot = collections.Counter(); allmonths = collections.Counter()
res = {}
for v in TIER:
    p = D / f"{v}.json"
    if not p.exists(): print(v, "SIN_DATO"); continue
    j = json.load(open(p, encoding="utf-8"))
    recs = j["records"] if isinstance(j, dict) and "records" in j else j
    c = collections.Counter(); first = min((r.get("datetime_utc","") for r in recs), default="")
    for r in recs:
        dt = (r.get("datetime_utc") or "")[:7]
        allmonths[(v, dt[:4])] += 1
        if dt >= "2026-01" and dt <= "2026-09":
            c[(bucket(r.get("sensor")), dt)] += 1
    res[v] = {f"{k[0]}|{k[1]}": n for k, n in sorted(c.items())}
    for k, n in c.items(): tot[k[0]] += n
    s = {b: sum(n for k, n in c.items() if k[0]==b) for b in ("MODIS","V750","V375")}
    print(f"{v:20s} total={len(recs):6d} primero={first[:10]} 2026-01..09: {s}  MODIS 2026-08={c[('MODIS','2026-08')]}")
print("Suma 11 Tier A 2026-01..09 por sensor:", dict(tot))
yrs = collections.Counter()
for (v, y), n in allmonths.items(): yrs[y] += n
print("Records por anio (11 Tier A):", dict(sorted(yrs.items())))
json.dump(res, open("records_por_mes.json","w",encoding="utf-8"), indent=1)
