"""F0 S175, 243: fracción de records MODIS con product_version nrt por mes, en la base 752d348bc (11 Tier A).
P1: si el Standard 6.1 dejara de llegar, la fracción nrt subiría (control: el campo existe y hay valores nrt recientes,
que esperan su upgrade). P2: columna sin_campo; si fuera todo sin_campo, el instrumento no mide."""
import io, json, sys
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\nmend\vrp-temporales\s175_audit\f0\base_data"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
c = defaultdict(Counter); dia = defaultdict(Counter); gran = Counter()
for v in VOLS:
    for r in json.load(open(f"{D}\{v}.json", encoding="utf-8"))["records"]:
        if not r["sensor"].startswith("MODIS"):
            continue
        pv = r.get("product_version", "sin_campo")
        c[r["datetime_utc"][:7]][pv] += 1
        if r["datetime_utc"] >= "2026-10-25":
            dia[r["datetime_utc"][:10]][pv] += 1
        if r["datetime_utc"] >= "2026-10-01":
            g = r.get("granule", "")
            gran[g.split(".")[3] if g.count(".") >= 4 else "?"] += 1
print("mes,versiones")
for m in sorted(c)[-8:]:
    tot = sum(c[m].values())
    print(m, dict(c[m]), f"nrt={round(100*c[m].get('nrt',0)/tot,1)}%")
print("\npor día desde 2026-10-25:")
for d in sorted(dia):
    print(d, dict(dia[d]))
print("\ncolección en el nombre del gránulo (records MODIS desde 2026-10-01):", dict(gran))
