"""Horas de runner y reloj de pared por run A/B (suma de duraciones de job; reloj = primer inicio a ultimo fin).
P1: un run con jobs muertos por timeout suma horas sin resultado; se separan success/no-success. P2: job sin
timestamps se cuenta en n_sin_ts, no como 0."""
import json, glob, re, sys, io
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def t(s): return datetime.fromisoformat(s.replace("Z","+00:00")) if s else None
for f in sorted(glob.glob("jobs_*.json")):
    rows = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    ok = bad = 0.0; sin = 0; ini = []; fin = []
    for r in rows:
        a, b = t(r["started_at"]), t(r["completed_at"])
        if not a or not b: sin += 1; continue
        h = (b - a).total_seconds()/3600; ini.append(a); fin.append(b)
        if r["conclusion"] == "success": ok += h
        else: bad += h
    wall = (max(fin) - min(ini)).total_seconds()/3600 if ini else None
    print(f"{f}: jobs={len(rows)} horas_ok={ok:.1f} horas_perdidas={bad:.1f} reloj_h={wall and round(wall,1)} sin_ts={sin}")
