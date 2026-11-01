"""Que publico MIROVA (data/mirova/NevadosDeChillan.json) en las dos pasadas donde el nucleo F5' cambia el nivel
(2026-10-10 06:30 y 2026-10-15 05:00 VIIRS_SNPP), +-60 min, mismo sensor VIIRS375. Tambien el caso 2026-10-18 06:48."""
import json, os, io, sys
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
m = json.load(open(os.path.join(ROOT,"data","mirova","NevadosDeChillan.json"),encoding="utf-8"))
recs = m["records"] + m.get("records_dia_ocr", [])
t = lambda s: datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
for obj, cl, f5 in [("2026-10-10 06:30",6.62,11.822),("2026-10-15 05:00",5.252,10.361),("2026-10-18 06:48",4.075,8.935)]:
    cerca = [r for r in recs if r.get("sensor") == "VIIRS375" and abs((t(r["datetime_utc"]) - t(obj)).total_seconds()) <= 3600]
    print(obj, "cumulo", cl, "nucleo", f5, "MIROVA:", [(r["datetime_utc"], r["VRP_MW"], r.get("clasificacion"), r.get("source"), r.get("distancia_km")) for r in cerca])
