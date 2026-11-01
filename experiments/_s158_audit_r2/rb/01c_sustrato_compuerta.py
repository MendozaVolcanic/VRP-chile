"""Afirmación 1, sustrato: en los records VIIRS 750 que existen SOLO por el segundo pase, ¿el píxel más caliente
de la escena fallaba la compuerta del primer pase (t_max - t_bg <= 3 K)? Si sí, en pass 1 NINGÚN píxel podía
pasar la compuerta, y la detección publicada salió entera por el camino sin compuerta. Campos del record:
se listan primero (pregunta 2: si no existieran, se imprime 'sin campo', no 0). Control: en los records con
primer pase > 0, t_max - t_bg debe ser > 3 K casi siempre (la compuerta lo exige para al menos un píxel)."""
import sys, io, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
VOLS = ["Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima","NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]
recs0 = json.load(open("data/mirova_equivalent/Lascar.json", encoding="utf-8")); recs0 = recs0["records"] if isinstance(recs0, dict) else recs0
ej = next(r for r in recs0 if r["sensor"].endswith("_750") and r.get("diag_n_second_pass_recapture"))
print("campos con 't_' o 'bg' en un record V750:", sorted(k for k in ej if "t_max" in k or "t_bg" in k or "bg_k" in k))
def dT(r):
    tm, tb = r.get("t_max_k"), r.get("t_bg_k")
    if tm is None: tm = r.get("diag_t_max_k")
    if tb is None: tb = r.get("diag_t_bg_k")
    return None if tm is None or tb is None else tm - tb
for desde in ("2025-02-15", "2026-09-18"):
    c = Counter()
    for v in VOLS:
        recs = json.load(open(f"data/mirova_equivalent/{v}.json", encoding="utf-8")); recs = recs["records"] if isinstance(recs, dict) else recs
        for r in recs:
            if not r["sensor"].endswith("_750") or (r.get("datetime_utc") or "") < desde: continue
            fp = r.get("diag_n_first_pass_pixels"); sp = r.get("diag_n_second_pass_recapture") or 0
            d = dT(r)
            if fp == 0 and sp > 0:
                c["solo_sp"] += 1
                if d is None: c["solo_sp_sin_campo"] += 1
                elif d <= 3.0: c["solo_sp_dT<=3"] += 1
                else: c["solo_sp_dT>3"] += 1
            elif fp and fp > 0:
                c["fp>0"] += 1
                if d is None: c["fp>0_sin_campo"] += 1
                elif d <= 3.0: c["fp>0_dT<=3"] += 1
                else: c["fp>0_dT>3"] += 1
    print(f"desde {desde}: {dict(c)}")
