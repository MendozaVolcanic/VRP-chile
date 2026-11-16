# -*- coding: utf-8 -*-
"""V33A, afirmacion 123/255: recomputar por otro camino la cadencia de nrt-healthcheck.yml (cron "0 12 * * *")
desde el insumo runs_nrt-healthcheck.json (50 corridas, lo que devolvio la API el 2026-11-07).
Pregunta 1: si el cron corriera a las 12:00 en punto, las horas de creacion serian 12:0x y el hueco maximo ~24 h.
Pregunta 2: si el insumo no se leyera, n=0 y se imprime. Control positivo: runs_nrt.json (cron cada 2 h) tiene
que dar huecos de ~2 h, no de ~24 h.
Uso: python -I v33a_cadencia_healthcheck.py <carpeta insumos>
"""
import io
import json
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
I = sys.argv[1]


def analizar(nombre):
    with open(f"{I}/{nombre}", encoding="utf-8") as fh:
        rs = json.load(fh)
    if isinstance(rs, dict):
        rs = rs.get("workflow_runs") or rs.get("runs") or []
    ts = sorted(datetime.strptime(r.get("createdAt") or r["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                for r in rs if r.get("event") == "schedule")
    print(f"== {nombre}: n={len(rs)} (0 = instrumento muerto); schedule={len(ts)}")
    if not ts:
        return
    horas = sorted(t.strftime("%H:%M") for t in ts)
    print(f"   ventana {ts[0]} a {ts[-1]}; hora de creacion min {horas[0]} max {horas[-1]} UTC")
    gaps = sorted(((b - a).total_seconds() / 3600, a) for a, b in zip(ts, ts[1:]))
    print(f"   hueco mediano {gaps[len(gaps)//2][0]:.2f} h; tres mayores: {[(round(g, 2), str(a)) for g, a in gaps[-3:]]}")
    tarde = [((t.hour * 60 + t.minute) - 12 * 60) / 60 for t in ts]
    print(f"   atraso respecto de las 12:00 UTC: min {min(tarde):.2f} h, mediana {sorted(tarde)[len(tarde)//2]:.2f} h, max {max(tarde):.2f} h")


analizar("runs_nrt-healthcheck.json")
analizar("runs_nrt.json")
