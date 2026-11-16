"""F0 S175: cadencia del NRT (¿«doce veces al día»?) y del healthcheck (255), con los insumos de la ola 0
(runs_nrt.json y runs_nrt-healthcheck.json, 50 corridas cada uno, bajados por el orquestador 2026-11-07 ~04:10 UTC).
P1: si el disparador externo muriera, las corridas workflow_dispatch caerían a 0 por día: se ve en la columna.
P2: con la lista vacía el script imprime n=0 y no da tasa."""
import io, json, sys
from collections import Counter
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
I = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
def t(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
for nombre in ("runs_nrt.json", "runs_nrt-healthcheck.json"):
    rs = json.load(open(f"{I}\{nombre}", encoding="utf-8"))
    print(f"\n== {nombre}: n={len(rs)}")
    if not rs: continue
    ts = sorted(t(r["createdAt"]) for r in rs)
    dias = (ts[-1] - ts[0]).total_seconds() / 86400
    ev = Counter(r["event"] for r in rs); con = Counter(r["conclusion"] for r in rs)
    print(f"ventana {ts[0]} a {ts[-1]} ({dias:.2f} días); por evento {dict(ev)}; conclusión {dict(con)}")
    if dias > 0:
        print(f"corridas por día: {len(rs)/dias:.1f}; dispatch por día {ev.get('workflow_dispatch',0)/dias:.1f}; schedule por día {ev.get('schedule',0)/dias:.1f}")
    porhora = Counter(x.strftime("%H:%M") for x in ts)
    print("horas de creación (UTC):", sorted(porhora.items())[:30])
    huecos = sorted(((b - a).total_seconds() / 3600, a) for a, b in zip(ts, ts[1:]))[-3:]
    print("tres huecos mayores entre corridas (h, desde):", [(round(h, 2), str(a)) for h, a in huecos])
