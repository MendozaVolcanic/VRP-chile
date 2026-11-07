#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175), afirmación 154: ¿el NRT re-escribe las 8 fechas de su ventana?
Pregunta 1: si el NRT re-escribiera los 8 días, cada record MODIS observado en los 8 días previos a la última
corrida tendría processed_utc posterior al encendido de la vía, y los observados entre el 2026-10-26 y el 2026-11-02
serían de la vía. Este conteo lo vería (cuenta por fecha de observación y por processed_utc).
Pregunta 2 (instrumento vivo): control positivo = los records de la vía existen y tienen processed_utc reciente; si
el lector no leyera processed_utc, el conteo post-encendido de la vía daría 0.
Además, mismo cálculo para VIIRS (que no cambió de detector): ¿cuántos records VIIRS de la ventana tienen
processed_utc de las últimas 24 h? Si el NRT re-escribiera, serían casi todos.
Uso: python reescritura_ventana.py <carpeta mirova_equivalent> <encendido ISO Z>
"""
import json, os, sys
from collections import Counter, defaultdict
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
carpeta, enc = sys.argv[1], sys.argv[2]
tab = defaultdict(Counter)
ult_proc = ""
recs_all = []
for v in VOLS:
    with open(os.path.join(carpeta, v + ".json"), encoding="utf-8") as fh:
        for r in json.load(fh).get("records") or []:
            recs_all.append((v, r))
            ult_proc = max(ult_proc, r.get("processed_utc") or "")
print("ultimo processed_utc del corpus:", ult_proc)
for v, r in recs_all:
    s = str(r.get("sensor") or "")
    fam = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
    obs = str(r.get("datetime_utc") or "")[:10]
    if obs < "2026-10-24":
        continue
    p = r.get("processed_utc") or ""
    via = r.get("via_codigo_mirova")
    tab[(fam, obs)][("post_enc" if p >= enc else "pre_enc", "via" if via is True else ("k" if via is None else str(via)),
                     r.get("product_version"))] += 1
for k in sorted(tab):
    print(k, dict(tab[k]))
# processed_utc en las ultimas 24 h por familia y fecha de observacion
from datetime import datetime, timedelta
t_ult = datetime.strptime(ult_proc, "%Y-%m-%dT%H:%M:%SZ")
lim = (t_ult - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
c24 = defaultdict(Counter)
for v, r in recs_all:
    s = str(r.get("sensor") or "")
    fam = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
    obs = str(r.get("datetime_utc") or "")[:10]
    if obs < "2026-10-30":
        continue
    c24[(fam, obs)]["proc_ultimas_24h" if (r.get("processed_utc") or "") >= lim else "proc_antes"] += 1
print("\nventana 24 h hasta", ult_proc, "(desde", lim, ")")
for k in sorted(c24):
    print(k, dict(c24[k]))
