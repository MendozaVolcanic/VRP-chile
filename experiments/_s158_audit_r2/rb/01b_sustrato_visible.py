"""Afirmación 1, sustrato visible: de los records VIIRS 750 de producción cuya detección existe SOLO por el
segundo pase (diag_n_first_pass_pixels == 0 y diag_n_second_pass_recapture > 0), cuántos quedan con
distance_class == 'summit' y primary_cluster.vrp_mw > 0 (lo que el tablero puede mostrar como anomalía de
cumbre; aproximación al predicado del tablero, no el predicado ejecutado con node). Ventanas: todo el corpus
y desde 2026-09-18. Pregunta 1: si ninguno fuera summit con magnitud, el conteo daría 0 y la cuestión sería
invisible; pregunta 2: el denominador se imprime."""
import sys, io, json, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = "data/mirova_equivalent"
VOLS = ["Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima","NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]
for desde in ("2025-02-15", "2026-09-18"):
    n = vis = 0; porv = Counter(); mags = []
    for v in VOLS:
        recs = json.load(open(f"{D}/{v}.json", encoding="utf-8")); recs = recs["records"] if isinstance(recs, dict) else recs
        for r in recs:
            if not r["sensor"].endswith("_750") or (r.get("datetime_utc") or "") < desde: continue
            if r.get("diag_n_first_pass_pixels") == 0 and (r.get("diag_n_second_pass_recapture") or 0) > 0:
                n += 1
                pc = r.get("primary_cluster") or {}
                if r.get("distance_class") == "summit" and (pc.get("vrp_mw") or 0) > 0:
                    vis += 1; porv[v] += 1; mags.append(pc["vrp_mw"])
    mags.sort()
    print(f"desde {desde}: solo-segundo-pase n={n}; de ellos summit con pc.vrp_mw>0: {vis} ({100*vis/max(1,n):.1f} %) | por volcán {dict(porv)} | mediana pc.vrp_mw {mags[len(mags)//2] if mags else None} MW, max {mags[-1] if mags else None}")
