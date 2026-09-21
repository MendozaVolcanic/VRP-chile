# -*- coding: utf-8 -*-
"""Frente G S149: cadencia real de los workflows con cron, 14 dias, contra el REMOTO.

Fuente: `gh api repos/.../actions/workflows/<yml>/runs?event=schedule&created=>=FECHA` paginado.
Denominador: corridas declaradas por el cron de cada yml (leidas a mano del yml y anotadas abajo).
Ventana: 14 dias cerrados hacia atras desde la hora del servidor.
Instrumento: 1) si el cron estuviera muerto daria 0 corridas: lo ve. 2) si gh fallara, total_count
ausente -> SIN DATO explicito. Control positivo: nrt.yml debe tener > 0 corridas.
Solo lectura: no despacha nada.
"""
import io, sys, json, subprocess, collections, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = sys.argv[1] if len(sys.argv) > 1 else "MendozaVolcanic/VRP-chile"
WFS = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {
    "nrt.yml": 12, "nrt-retry.yml": 12, "pages-deploy.yml": 12, "sync-mirova-csv.yml": 24,
    "nrt-monitor.yml": None, "nrt-healthcheck.yml": None, "audit-weekly.yml": None,
    "reproc-watchdog.yml": None, "tests.yml": None}
ahora = dt.datetime.now(dt.timezone.utc)
desde = (ahora - dt.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
print("ahora UTC", ahora.isoformat(timespec="seconds"), "desde", desde)
for wf, esp in WFS.items():
    runs, page = [], 1
    while True:
        out = subprocess.run(["gh", "api", f"repos/{REPO}/actions/workflows/{wf}/runs?event=schedule"
                              f"&created=>={desde}&per_page=100&page={page}"],
                             capture_output=True, text=True, encoding="utf-8")
        if out.returncode != 0:
            print(f"{wf:26s} SIN DATO ({out.stderr.strip()[:80]})")
            runs = None
            break
        j = json.loads(out.stdout)
        runs += j["workflow_runs"]
        if len(j["workflow_runs"]) < 100:
            break
        page += 1
    if runs is None:
        continue
    concl = collections.Counter((r["conclusion"] or r["status"]) for r in runs)
    pordia = collections.Counter(r["created_at"][:10] for r in runs)
    ult = max((r["created_at"] for r in runs), default="-")
    ult_ok = max((r["created_at"] for r in runs if r["conclusion"] == "success"), default="-")
    pct = f"{100 * len(runs) / (esp * 14):.0f} % de {esp * 14}" if esp else "sin cron horario declarado aca"
    print(f"{wf:26s} n={len(runs):4d} ({pct}) {dict(concl)} ultimo={ult} ultimo_ok={ult_ok}")
    if esp:
        print("   por dia:", " ".join(f"{d[5:]}:{pordia[d]}" for d in sorted(pordia)))
