"""F3: ¿dónde está el escalón C0->K en la serie que ve el operador? Pasadas nocturnas VIIRS 375 con 'dash' del
auto-audit (mismo predicado que coincidió con node en 211 de 211 noches pos, falsas_y_recall_por_regimen.py), por
semana, Nevados de Chillán y los 11 juntos, 2026-08-28..2026-10-18. La marca del tablero está en 2026-10-18 09:57
(frontend/cambio_detector.js:16). P1: si el escalón estuviera en 10-18, la fracción caería ahí y no en 09-18.
P2: n por semana impreso."""
import json, os, sys
from datetime import date, datetime, timezone, timedelta
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa
from pareado_k_vs_sombra import dash  # noqa
coords = aw._coords_por_volcan()
agg = defaultdict(lambda: [0, 0])
for vol in aw.VOLS:
    for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]:
        d = r["datetime_utc"][:10]
        if not ("2026-08-28" <= d <= "2026-10-18") or aw.our_bucket(r["sensor"]) != "VIIRS375": continue
        o = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if aw.es_pasada_diurna_descartada("VIIRS375", *coords[vol], o): continue
        dd = date.fromisoformat(d); sem = (dd - timedelta(days=(dd - date(2026, 9, 18)).days % 7)).isoformat()
        for k in (("11", sem), (vol, sem)):
            agg[k][0] += 1; agg[k][1] += int(dash(r, vol) > 0)
for g in ("11", "NevadosDeChillan"):
    print(g)
    for (gg, sem), (n, p) in sorted(agg.items()):
        if gg == g: print(f"  semana desde {sem}: {p}/{n} pasadas publican ({100*p/n:.1f} %)")
