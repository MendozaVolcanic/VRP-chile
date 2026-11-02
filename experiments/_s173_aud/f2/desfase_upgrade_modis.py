# -*- coding: utf-8 -*-
"""S173 F2 hallazgo 207: ¿cuántos días ANTES del merge cae la primera pasada MODIS re-escrita por la vía?
Mide, en los records MODIS de producción (data/mirova_equivalent de main a3c5a9b49, worktree s173-f2-combo), el desfase
entre la observación (datetime_utc) y la última escritura (processed_utc) de los records que fueron re-escritos después
de su primera escritura (processed_utc > first_processed_utc), ventana 2026-10-01 a 2026-11-02 (régimen K, NRT de hoy).
Es el desfase con que el NRT re-escribe una pasada vieja: tras el merge de B, esa re-escritura sale de la vía.
Pregunta 1: si no hubiera re-escrituras, n = 0 y se dice SIN DATO. Pregunta 2: control: los records nunca re-escritos
(processed_utc == first_processed_utc) tienen que tener desfase chico (horas), distinto del de los re-escritos."""
import json, sys, statistics
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")
WT = sys.argv[1]
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
        "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
def t(s):
    s = str(s or "").replace("Z", "").replace("T", " ")[:19]
    try: return datetime.fromisoformat(s)
    except ValueError: return None
re_esc, una, vers = [], [], {}
nrt_re, nrt_una = [], []
for v in VOLS:
    for r in json.load(open(f"{WT}/data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]:
        if not str(r.get("sensor") or "").startswith("MODIS"): continue
        obs, pr, fp = t(r.get("datetime_utc")), t(r.get("processed_utc")), t(r.get("first_processed_utc"))
        if not (obs and pr) or not ("2026-10-01" <= str(r.get("datetime_utc"))[:10] <= "2026-11-02"): continue
        vers[r.get("product_version")] = vers.get(r.get("product_version"), 0) + 1
        d = (pr - obs).total_seconds() / 86400
        (re_esc if (fp and pr > fp) else una).append(d)
        # refinamiento: sólo records cuya PRIMERA escritura fue del NRT en tiempo casi real (< 1 día tras la observación)
        if fp and (fp - obs).total_seconds() / 86400 < 1.0:
            (nrt_re if pr > fp else nrt_una).append(d)
def q(xs, p): xs = sorted(xs); return round(xs[min(len(xs) - 1, int(p * (len(xs) - 1)))], 2)
print("records MODIS de los 11, observados 2026-10-01 a 2026-11-02; product_version:", vers)
for nom, xs in (("re-escritos (processed > first_processed)", re_esc), ("escritos una vez (control)", una),
                ("NRT casi real (primera escritura < 1 día) y re-escritos", nrt_re), ("NRT casi real y nunca re-escritos (control)", nrt_una)):
    if not xs: print(nom, "SIN DATO (n=0)"); continue
    print(f"{nom}: n={len(xs)}, desfase obs->última escritura en días: mediana {round(statistics.median(xs),2)}, p90 {q(xs,.9)}, máx {round(max(xs),2)}")
