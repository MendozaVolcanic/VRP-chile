# Verificador S156: cobertura por volcan/sensor/dia de produccion (con y sin sha) y sombra en la ventana
import json, sys, collections
from pathlib import Path
W = Path(sys.argv[1]); WIN = ("2026-09-18", "2026-10-19")
VOLS = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
def b(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else None))
tot = collections.Counter()
for vol in VOLS:
    for sub in ("mirova_equivalent", "experimental_v2"):
        d = json.load(open(W/"data"/sub/f"{vol}.json", encoding="utf-8"))
        rs = [r for r in d["records"] if WIN[0] <= r.get("datetime_utc","")[:10] <= WIN[1]]
        dias = sorted({r["datetime_utc"][:10] for r in rs})
        sha = collections.Counter(((r.get("regimen") or {}).get("codigo_sha") or "SIN_SHA")[:8] for r in rs)
        perf = collections.Counter(((r.get("regimen") or {}).get("perfil") or "SIN") for r in rs)
        bs = collections.Counter(b(r.get("sensor")) for r in rs)
        print(f"{vol:20s} {sub:18s} n={len(rs):5d} dias={dias[0] if dias else None}..{dias[-1] if dias else None} ndias={len(dias)} sha={dict(sha)} perfil={dict(perf)} buckets={dict(bs)}")
        # claves de regimen disponibles
        for r in rs[:1]:
            tot[(sub, tuple(sorted((r.get('regimen') or {}).keys())))] += 1
print(tot)
