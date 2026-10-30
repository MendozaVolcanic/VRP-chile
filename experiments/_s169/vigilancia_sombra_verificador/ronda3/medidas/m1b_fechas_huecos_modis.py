# Fechas exactas de los dias sin record MODIS (Isluga, Lascar), data/mirova_equivalent, 2026-03-01..2026-10-14 (228 dias).
# Si son huecos de orbita, deberian repetirse cada 16 dias (repeticion de Terra/Aqua). Solo describe, no prueba CMR.
import json, datetime as dt, sys
sys.path.insert(0, "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/arbol")
from scripts.revisar_sombra import familia
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent/"
A, B = dt.date(2026,3,1), dt.date(2026,10,14)
for v in ["Isluga","Lascar"]:
    d = json.load(open(R+v+".json", encoding="utf-8")); recs = d["records"] if isinstance(d, dict) else d
    por = {}
    for r in recs:
        if familia(r.get("sensor")) == "MODIS":
            por.setdefault(str(r.get("datetime_utc"))[:10], set()).add(r.get("sensor"))
    falt = [A+dt.timedelta(days=i) for i in range((B-A).days+1) if (A+dt.timedelta(days=i)).isoformat() not in por]
    print(v, [x.isoformat() for x in falt], "sensores vistos:", sorted({s for x in por.values() for s in x}))
    # dias con un solo satelite MODIS
    uno = [k for k,x in por.items() if A.isoformat()<=k<=B.isoformat() and len(x)==1]
    print(v, "dias con un solo satelite MODIS:", len(uno))
