"""Concurrencia de jobs A/B S135 (runs 34173711390 + 34208191011) contra jobs NRT del 2026-09-08,
y espera en cola de los jobs NRT (started_at - created_at). Limite GitHub repo publico: 20 jobs (SOSPECHA, citado
en reproc-chunked.yml:51, no verificado contra docs de GitHub en esta sesion).
P1: si hubiera saturacion, la concurrencia maxima tocaria 20 y la espera NRT creceria. P2: si faltan timestamps
el job se descarta y se cuenta aparte (n_sin_ts)."""
import json, glob, sys, io
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def t(s): return datetime.fromisoformat(s.replace("Z","+00:00")) if s else None
ev = []; sin = 0; nrt = []
for f in ["jobs_34173711390.json", "jobs_34208191011.json"] + glob.glob("nrtjobs_*.json"):
    for l in open(f, encoding="utf-8"):
        if not l.strip(): continue
        j = json.loads(l); a, b = t(j["started_at"]), t(j["completed_at"])
        if not a or not b: sin += 1; continue
        kind = "NRT" if f.startswith("nrt") else "AB"
        ev += [(a, 1, kind), (b, -1, kind)]
        if kind == "NRT" and j.get("created_at"): nrt.append((a - t(j["created_at"])).total_seconds()/60)
ev.sort(key=lambda x: (x[0], x[1])); cur = {"AB":0,"NRT":0}; mx = (0, None, None)
for ts, dlt, k in ev:
    cur[k] += dlt; tot = cur["AB"] + cur["NRT"]
    if tot > mx[0]: mx = (tot, ts, dict(cur))
print("concurrencia maxima AB+NRT:", mx, "jobs sin timestamps:", sin)
if nrt:
    nrt.sort(); print("espera en cola jobs NRT (min): mediana", round(nrt[len(nrt)//2],1), "max", round(nrt[-1],1), "n", len(nrt))
