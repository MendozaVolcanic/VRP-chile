"""Cadencia del cron NRT (nrt.yml) en los ultimos 14 dias, desde gh run list.
Pregunta 1: si el cron estuviera muerto, aqui se veria 0 runs/dia. Si.
Pregunta 2: si gh estuviera muerto, el JSON no existiria o tendria 0 filas (se declara N).
Control positivo: el cron es cada 2 h -> esperamos ~12 runs/dia; un dia con 12 confirma que el conteo ve runs.
Ventana: NOW (fecha del servidor) menos 14 dias. Denominador: runs con event=schedule.
"""
import json, sys, io
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
NOW = datetime(2026, 9, 13, 11, 49, tzinfo=timezone.utc)  # header Date del servidor
d = json.load(open("experiments/_s138_audit/eje6/nrt_runs.json"))
print("N runs descargados:", len(d), "rango:", d[-1]["createdAt"], "->", d[0]["createdAt"])
print("eventos:", Counter(r["event"] for r in d))
print("ramas:", Counter(r["headBranch"] for r in d))
runs = [r for r in d if r["event"] == "schedule"]
runs = [dict(r, t=datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))) for r in runs]
runs.sort(key=lambda r: r["t"])
w = [r for r in runs if r["t"] >= NOW - timedelta(days=14)]
print(f"\nVentana 14 d: {NOW - timedelta(days=14):%Y-%m-%d %H:%M} -> {NOW:%Y-%m-%d %H:%M} UTC; runs schedule en ventana: {len(w)} (esperados 12/dia x 14 = 168)")
por_dia = defaultdict(Counter)
for r in w:
    por_dia[r["t"].date()][r["conclusion"] or r["status"]] += 1
print("\ndia | total | success | failure | otros")
tot = Counter()
for day in sorted(por_dia):
    c = por_dia[day]
    otros = sum(v for k, v in c.items() if k not in ("success", "failure"))
    print(f"{day} | {sum(c.values())} | {c['success']} | {c['failure']} | {otros} {dict(c) if otros else ''}")
    tot.update(c)
print("TOTAL ventana:", dict(tot))
print("\nHuecos > 4 h entre runs schedule consecutivos (ventana 14 d):")
prev = None
n_gaps = 0
for r in w:
    if prev is not None:
        dt = (r["t"] - prev).total_seconds() / 3600
        if dt > 4:
            n_gaps += 1
            print(f"  {prev:%Y-%m-%d %H:%M} -> {r['t']:%Y-%m-%d %H:%M}  = {dt:.1f} h")
    prev = r["t"]
dt_last = (NOW - w[-1]["t"]).total_seconds() / 3600
print(f"  ultimo run schedule -> ahora: {dt_last:.1f} h")
print("huecos >4 h:", n_gaps)
# comparacion con la ventana completa descargada
print("\nVentana completa descargada (schedule):", len(runs), "runs entre", runs[0]["t"], "y", runs[-1]["t"])
dias = (runs[-1]["t"] - runs[0]["t"]).total_seconds() / 86400
print(f"  runs/dia promedio: {len(runs)/dias:.2f} (esperado 12)")
