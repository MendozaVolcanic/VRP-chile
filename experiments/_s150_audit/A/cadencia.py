"""S150 frente A: cadencia real de cada cron (eventos schedule) contra la declarada.
Instrumento: gh api actions/runs (paginado, tope de 1000 resultados de la API: la ventana efectiva
se informa abajo y es la que manda). P1: si un cron dejara de llegar, su conteo caeria y el hueco
maximo creceria (lo ve). P2: si la API no devolviera nada, n=0 y se informa SIN DATO.
Control positivo: los workflow_run de pages-deploy siguen al NRT, deben ser ~igual de frecuentes."""
import sys, csv, statistics
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")
DECL = {"nrt.yml": 2.0, "sync-mirova-csv.yml": 1.0, "nrt-monitor.yml": 6.0,
        "nrt-healthcheck.yml": 24.0, "nrt-retry.yml": None, "pages-deploy.yml": None,
        "reproc-watchdog.yml": None, "audit-weekly.yml": 168.0}
rows = [l.rstrip("\n").split("\t") for l in open("runs_30d.tsv", encoding="utf-8")]
t = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
ini = min(t(r[4]) for r in rows); fin = max(t(r[4]) for r in rows)
print(f"ventana efectiva: {ini:%Y-%m-%d %H:%M} a {fin:%Y-%m-%d %H:%M} UTC ({(fin-ini).total_seconds()/86400:.1f} d), n={len(rows)} corridas")
for wf in sorted({r[2].split('/')[-1] for r in rows}):
    ts = sorted(t(r[4]) for r in rows if r[2].endswith(wf) and r[3] == "schedule")
    if len(ts) < 3: continue
    d = [(b - a).total_seconds() / 3600 for a, b in zip(ts, ts[1:])]
    span = (ts[-1] - ts[0]).total_seconds() / 3600
    print(f"{wf:28s} n={len(ts):4d} declarado={DECL.get(wf)} h  mediana={statistics.median(d):.2f} h  "
          f"media={span/(len(ts)-1):.2f} h  p90={sorted(d)[int(.9*len(d))]:.2f} h  max={max(d):.2f} h")
