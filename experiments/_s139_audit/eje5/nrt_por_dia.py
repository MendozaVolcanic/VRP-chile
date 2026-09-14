"""Corridas del cron NRT por dia UTC, 2026-08-14..2026-09-13 (API GitHub, workflow nrt.yml).
P1: si el cron corriera 12/dia como declara `0 */2 * * *`, la mediana seria 12; si no corre, 0. P2: si la API
no devuelve runs, el archivo queda vacio y se reporta SIN_DATO. Control positivo: hoy hubo commits 'NRT update'."""
import collections, statistics as st, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
rows = [l.rstrip("\n").split("\t") for l in open("nrt_runs_30d.tsv", encoding="utf-8") if l.strip()]
if not rows: print("SIN_DATO"); sys.exit()
d = collections.Counter(r[1][:10] for r in rows); ev = collections.Counter(r[5] for r in rows)
con = collections.Counter(r[4] for r in rows)
full = [d[k] for k in sorted(d) if "2026-08-15" <= k <= "2026-09-12"]
print("runs:", len(rows), "eventos:", dict(ev), "conclusion:", dict(con))
print("por dia (dias completos 08-15..09-12): mediana", st.median(full), "min", min(full), "max", max(full), "n_dias", len(full))
print(dict(sorted(d.items())))
