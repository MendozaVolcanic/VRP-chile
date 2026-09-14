"""Duracion real de jobs de reproceso/A-B (eje 5, S139).
Instrumento: timestamps de la API de GitHub (started_at/completed_at del step 'Run reprocess' o equivalente).
P1 (si estuviera roto, lo veria?): un job que no proceso nada dura segundos; se reporta dur y conclusion.
P2 (instrumento muerto): si la API no devuelve steps, la fila sale SIN_DATO, no 0.
Control positivo: los jobs 'failure'/'cancelled' deben aparecer con su conclusion.
Ventanas (dias por job) salen de ventanas_runs.sh (lineas '>>> Volcan | fecha' del log de un job)."""
import json, glob, statistics as st, sys, io, re
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DIAS = {"29437771858":90,"29582035729":90,"33370202265":89,"33412422099":88,"33456630043":88,
        "33872821788":31,"33872836355":61,"33912398561":61,"34173711390":45,"34208191011":47}
def t(s): return datetime.fromisoformat(s.replace("Z","+00:00")) if s else None
out = {}
for f in sorted(glob.glob("jobs_*.json")):
    rid = re.search(r"jobs_(\d+)", f).group(1)
    rows = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    print(f"\n=== run {rid}  jobs={len(rows)}  dias_por_job={DIAS.get(rid,'SIN_DATO')}")
    durs = []
    for r in rows:
        step = next((s for s in r["steps"] if re.search(r"reprocess|Run pipeline|Run reproc|probe|bateria|Correr", s["name"], re.I)), None)
        if step and step["started_at"] and step["completed_at"]:
            d = (t(step["completed_at"]) - t(step["started_at"])).total_seconds()/60
        else:
            d = None
        jd = (t(r["completed_at"]) - t(r["started_at"])).total_seconds()/60 if r["started_at"] and r["completed_at"] else None
        print(f"  {r['name'][:70]:70s} {r['conclusion']:10s} job={jd and round(jd,1)} step={d and round(d,1)}")
        if d is not None and r["conclusion"]=="success": durs.append((r["name"], d))
    if durs and rid in DIAS:
        per = [d/DIAS[rid] for _, d in durs]
        print(f"  -> min/dia: mediana {st.median(per):.2f}  max {max(per):.2f}  n={len(per)}")
        out[rid] = {"dias": DIAS[rid], "min_dia": [(n, round(d/DIAS[rid],3)) for n, d in durs]}
json.dump(out, open("duraciones.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
