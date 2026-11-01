"""F3: ¿las bandas del auto-audit pueden dispararse? Para cada lunes desde 2026-03-02, cuenta las noches
con alerta nocturna de MIROVA por sensor en la ventana rodante de 60 días (mismo filtro que main():
alertas_mirova + es_pasada_diurna_descartada, sólo los 11 VOLS), y las compara con MIN_N_RECALL.
Cuenta también cuántas noches-volcán por volcán y sensor caben en la ventana (MIN_N_RATIO).
P1: si las bandas tuvieran poder, el conteo superaría el mínimo; P2: imprime n en cada lunes (0 explícito).
Las alertas protegidas (>= 1 MW, lectura A sin D-9) se cuentan aparte: el audit no tiene criterio para ellas."""
import sys, os
from collections import defaultdict, Counter
from datetime import date, timedelta, datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa
coords = aw._coords_por_volcan()
noches = defaultdict(float)
for a in aw.alertas_mirova():
    dt = a["fecha_utc"] or ""
    if a["volcano"] not in aw.VOLS or a["sensor_bucket"] not in aw.SENSORS or not dt[:4].isdigit(): continue
    try: o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
    except ValueError: continue
    ll = coords.get(a["volcano"])
    if ll and aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o): continue
    k = (a["volcano"], a["sensor_bucket"], dt[:10]); noches[k] = max(noches[k], a["vrp_mw"] or 0)
d = date(2026, 3, 2); filas = []
while d <= date(2026, 10, 19):
    w0 = (d - timedelta(days=aw.WINDOW_DAYS)).isoformat(); w1 = d.isoformat()
    c = Counter(s for (v, s, n) in noches if w0 <= n <= w1)
    prot = Counter(s for (v, s, n), m in noches.items() if w0 <= n <= w1 and m >= 1.0)
    filas.append((w1, dict(c), dict(prot)))
    print(w1, "noches con alerta:", {s: c.get(s, 0) for s in aw.SENSORS}, "| protegidas:", {s: prot.get(s, 0) for s in aw.SENSORS},
          "| MODIS flaggeable:", c.get("MODIS", 0) >= aw.MIN_N_RECALL)
    d += timedelta(days=7)
