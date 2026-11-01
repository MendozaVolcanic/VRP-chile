# -*- coding: utf-8 -*-
"""F1 (S158): en la ventana K, ¿cuántas detecciones de VIIRS 750 vienen SOLO del segundo pase (primer pase vacío)?
El segundo pase no lleva la compuerta bt > t_bg + 3 K (detection_context.py:958) y corre aunque el primero esté vacío
(ENABLE_SECOND_PASS_CONDITIONED = False). Instrumento 1: si el segundo pase nunca agregara nada, la cuenta sería 0.
Instrumento 2: records sin los diag de pase se cuentan aparte. Uso: python -B experiments/_s158_audit/f1/primer_pase_vacio.py"""
import io, json, os, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
VOLS = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
        "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
P = {(p["v"], p["t"], p["s"]): p for p in json.load(open(os.path.join(AQUI, "pub_v750.json"), encoding="utf-8"))}
c = Counter()
for v in VOLS:
    for r in json.load(open(os.path.join(RAIZ, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        if not str(r.get("sensor", "")).endswith("_750") or r["datetime_utc"] < "2026-09-18":
            continue
        fp, sp = r.get("diag_n_first_pass_pixels"), r.get("diag_n_second_pass_recapture")
        if fp is None or sp is None:
            c["sin_dato"] += 1; continue
        pub = P[(v, r["datetime_utc"], r["sensor"])]["pub"] > 0
        c["n"] += 1
        if fp + sp > 0: c["con_deteccion"] += 1
        if fp == 0 and sp > 0:
            c["solo_segundo_pase"] += 1; c["solo_segundo_pase_publicado"] += pub
        if pub: c["publicados"] += 1
print(dict(c))
