"""Detector de zombies por volcan (Tier A): ultimo record (datetime_utc / processed_utc) en
data/mirova_equivalent/<V>.json leido de origin/main (nunca del checkout), records por dia en los
ultimos 14 dias, y fecha del ultimo commit REMOTO que toco el archivo (gh api).
Pregunta 1: si el pipeline no produjera, el ultimo processed_utc se quedaria viejo y los dias recientes darian 0. Si.
Pregunta 2: si el script no leyera el JSON, fallaria con excepcion (no hay cero silencioso; se imprime N total).
Control positivo/negativo: los 11 Tier A deben tener records en los ultimos 2 dias; dos volcanes fuera del cron
(ventana abril-2026) deben dar 0 recientes -> el instrumento distingue viejo de no-medido.
Ventana: 2026-08-30 11:49 -> 2026-09-13 11:49 UTC (14 d). Denominador por volcan: records con datetime_utc en ventana.
"""
import json, subprocess, sys, io
from datetime import datetime, timedelta, timezone
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
NOW = datetime(2026, 9, 13, 11, 49, tzinfo=timezone.utc)
W0 = NOW - timedelta(days=14)
TIER_A = ["Lastarria", "Lascar", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten",
          "PlanchonPeteroa", "Tupungatito", "Copahue", "PuyehueCordonCaulle"]
CONTROL = ["Calbuco", "Osorno"]
def load(name):
    raw = subprocess.run(["git", "show", f"origin/main:data/mirova_equivalent/{name}.json"], capture_output=True).stdout
    return json.loads(raw)
def remote_commit(name):
    out = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/VRP-chile/commits?path=data/mirova_equivalent/{name}.json&per_page=1",
                          "--jq", ".[0] | [.commit.committer.date, .sha[0:9], .commit.message] | @tsv"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return out.stdout.strip().replace("\t", " | ")[:110]
print(f"ventana: {W0:%Y-%m-%d %H:%M} -> {NOW:%Y-%m-%d %H:%M} UTC\n")
print("volcan | N total | ultimo datetime_utc | ultimo processed_utc | updated | rec 14d | dias con rec /14 | h desde ult. processed | ultimo commit remoto")
rows = []
for v in TIER_A + CONTROL:
    d = load(v)
    recs = d["records"]
    dts = [datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) for r in recs]
    pr = [r.get("processed_utc") for r in recs if r.get("processed_utc")]
    last_p = max(pr) if pr else "-"
    inw = [t for t in dts if t >= W0]
    days = len({t.date() for t in inw})
    lp = datetime.fromisoformat(last_p.replace("Z", "+00:00")) if last_p != "-" else None
    h = f"{(NOW - lp).total_seconds()/3600:.1f}" if lp else "-"
    rc = remote_commit(v)
    print(f"{v} | {len(recs)} | {max(dts):%Y-%m-%d %H:%M} | {last_p} | {d.get('updated')} | {len(inw)} | {days} | {h} | {rc}")
    rows.append((v, len(recs), len(inw), days))
print("\nRecords por dia (datetime_utc) en ventana, 11 Tier A sumados:")
c = Counter()
for v in TIER_A:
    for r in load(v)["records"]:
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if t >= W0: c[t.date()] += 1
for k in sorted(c): print(" ", k, c[k])
