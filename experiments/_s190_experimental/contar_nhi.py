# -*- coding: utf-8 -*-
"""S190: cuantas escenas SWIR (NHI-v1, Sentinel 2 y Landsat 8/9) hay por volcan Tier A, en total y desde que
existe la serie del laboratorio (2026-10-02), y cuantas con alerta.

POR QUE. La vara SWIR del laboratorio es NHI-v1 (docs/audit_s149/plan_final/FRENTE_F_EXPERIMENTAL.md §3). Antes de
pre-registrar un criterio hay que saber si hay escenas suficientes para que el criterio pueda dar distinto de cero
(A116). Lee la salida publicada del repo hermano por la API (regla 4 del mapa del workspace: nunca su disco).
"""
import json, subprocess, sys
from urllib.parse import quote
from urllib.request import urlopen

TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
          "Chaiten", "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-10-02"
print(f"{'volcan':22} {'escenas':>7} {'alerta':>6} {'desde '+DESDE:>17} {'alerta':>6}  rango")
tot = [0, 0, 0, 0]
# NHI-v1 nombra las carpetas con espacios y guiones (A14: buscar todas las variantes de nombre)
NOMBRE_NHI = {"PuyehueCordonCaulle": "Puyehue - Cordon Caulle", "PlanchonPeteroa": "Planchon-Peteroa",
              "NevadosDeChillan": "Nevados de Chillan"}
for v in TIER_A:
    carpeta = quote(NOMBRE_NHI.get(v, v))
    r = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/NHI-v1/contents/docs/nhi_data/{carpeta}/nhi_timeseries.json",
                        "--jq", ".download_url"], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"{v:22} SIN SERIE (la API responde error: {r.stdout.strip()[:60] or r.stderr.strip()[:60]})")
        continue
    d = json.load(urlopen(r.stdout.strip()))
    filas = [x for x in d if isinstance(x, dict)]
    rec = [x for x in filas if x.get("fecha", "") >= DESDE]
    fila = [len(filas), sum(bool(x.get("alerta")) for x in filas), len(rec), sum(bool(x.get("alerta")) for x in rec)]
    tot = [a + b for a, b in zip(tot, fila)]
    f = sorted(x.get("fecha", "") for x in filas)
    print(f"{v:22} {fila[0]:>7} {fila[1]:>6} {fila[2]:>17} {fila[3]:>6}  {f[0]} a {f[-1]}")
print(f"{'TOTAL':22} {tot[0]:>7} {tot[1]:>6} {tot[2]:>17} {tot[3]:>6}")
