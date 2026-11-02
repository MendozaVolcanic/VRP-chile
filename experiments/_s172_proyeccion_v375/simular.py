# -*- coding: utf-8 -*-
import json, random, collections, statistics as st
from datetime import date, timedelta
S = json.load(open("series.json", encoding="utf-8"))
INI = date(2026,11,3)
def semanas(clave):
    v = list(S[clave]["serie"].values()); return [v[7*i:7*i+7] for i in range(8)]
def correr(clave, g, escala=1.0, n=20000, seed=1):
    rng = random.Random(seed); W = semanas(clave); out = []; alerta_liga = 0; noches_hasta = []
    for _ in range(n):
        noches = alertas = 0; i = 0; bloque = []
        while True:
            if not bloque: bloque = list(rng.choice(W))
            a = bloque.pop(0)
            if escala != 1.0: a = sum(1 for _ in range(a) if rng.random() < escala)
            if rng.random() >= g:           # la noche tiene dato
                noches += 1; alertas += a
                if noches >= 30 and alertas >= 40: break
            i += 1
            if i > 400: break
        out.append(INI + timedelta(days=i)); alerta_liga += (noches_tot := 0)
        noches_hasta.append(i + 1)
    out.sort(); q = lambda p: out[int(p*(len(out)-1))]
    # parada limitada por alertas: la fecha es mayor que la del noche 30 sin huecos
    return {"p5": q(.05).isoformat(), "p50": q(.5).isoformat(), "p95": q(.95).isoformat(), "max": out[-1].isoformat(),
            "min": out[0].isoformat()}
res = {}
for clave in ("todas", "sin_chillan", "solo_tabla"):
    for g in (0.0, 1/152, 1/56, 0.05, 0.10, 0.20):
        for esc in (1.0, 0.5, 0.35):
            res[f"{clave}|g={g:.4f}|esc={esc}"] = correr(clave, g, esc)
for k, v in res.items(): print(k, v)
json.dump(res, open("sim.json","w"), indent=1)
