# -*- coding: utf-8 -*-
"""F3 R10. La auditoria semanal (scripts/auto_audit_weekly.py:319, load_mirova_alertas CONS U OCR) cuenta una
noche positiva si hay alguna alerta. ¿Cuantas noches positivas de su ventana vigente (2026-08-06 a 2026-10-05,
data/audit_continuous/latest.json) se sostienen SOLO en filas del OCR, y de esas cuantas solo en pasadas que
nuestro record pareado identifica como Suomi NPP (el canal con imagen de otra pasada, S150)?
P1: si el OCR no pesara, el conteo seria 0. P2: control: el total de noches V375 debe quedar cerca de 194 + las
noches sin datos nuestros (la semanal excluye esas desde S150); si da muy distinto, el cruce no es el mismo.
No filtra diurno por elevacion solar (aproximacion: hora UTC 00-12); se declara."""
import sys, json, collections, bisect
from datetime import datetime, timedelta
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
from pipeline.mirova_csv_loader import load_mirova_alertas
SNAP = RAIZ / "data/mirova_reference/mirova_v1_snapshot"
al = load_mirova_alertas(cons_path=str(SNAP / "registro_vrp_consolidado.csv"), ocr_path=str(SNAP / "registro_vrp_ocr.csv"))
print("tipo", type(al), "ejemplo", (al[0] if isinstance(al, list) else next(iter(al))) if al else None)
idx = collections.defaultdict(list)
for p in (RAIZ / "data" / "mirova_equivalent").glob("*.json"):
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except Exception: continue
    for r in d.get("records", []):
        s = r.get("sensor") or ""
        if s.startswith("VIIRS") and not s.endswith("_750") and r.get("datetime_utc"):
            idx[p.stem].append((r["datetime_utc"][:16], s))
for v in idx.values(): v.sort()
def sat(f):
    l = idx.get(f["volcano"], []); t = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
    ts = [x[0] for x in l]; i = bisect.bisect_left(ts, (t - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M"))
    if i < len(l) and l[i][0] <= (t + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M"): return l[i][1]
    return "sin record"
noches = collections.defaultdict(list)
for f in al:
    if f["sensor_bucket"] != "VIIRS375" or not ("2026-08-06" <= f["fecha_utc"][:10] <= "2026-10-05"): continue
    if f["fecha_utc"][11:13] >= "12": continue
    noches[(f["volcano"], f["fecha_utc"][:10])].append(f)
solo_ocr = {k: v for k, v in noches.items() if all(x["source"] == "OCR" for x in v)}
solo_snpp = {k: v for k, v in solo_ocr.items() if all("SNPP" in sat(x) for x in v)}
print("noches V375 con alerta (UTC 00-12):", len(noches), "| sostenidas solo por OCR:", len(solo_ocr), "| solo por OCR de Suomi NPP:", len(solo_snpp))
print("   por volcan (solo OCR SNPP):", dict(collections.Counter(k[0] for k in solo_snpp)))
