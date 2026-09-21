"""Frente F, S149. Frescura de las series de los perfiles de laboratorio, en disco.

Instrumento:
1. Si la serie estuviera abandonada, esto lo ve: reporta el ultimo datetime_utc por volcan.
2. Control positivo: data/mirova_equivalent (corre cada 2 h) debe dar fecha de hoy o ayer.
   Un directorio inexistente se reporta como NO EXISTE, distinto de vacio.
Denominador: todos los *.json del directorio. Ventana: toda la serie.
"""
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito",
          "PlanchonPeteroa", "Chaiten", "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]

for sub in ["mirova_equivalent", "experimental", "experimental_v2",
            "experimental_ndc_focus", "experimental_lowT"]:
    d = os.path.join(REPO, "data", sub)
    if not os.path.isdir(d):
        print(f"\n## data/{sub}: NO EXISTE en disco")
        continue
    archivos = sorted(glob.glob(os.path.join(d, "*.json")))
    print(f"\n## data/{sub}: {len(archivos)} archivos json")
    filas = []
    for a in archivos:
        try:
            with open(a, encoding="utf-8") as f:
                j = json.load(f)
        except Exception as e:  # noqa
            filas.append((os.path.basename(a), "ILEGIBLE", str(e)[:40], 0, 0))
            continue
        recs = j if isinstance(j, list) else j.get("records", j.get("data", []))
        fechas = sorted(r.get("datetime_utc", "") for r in recs if isinstance(r, dict))
        n_vrp = sum(1 for r in recs if isinstance(r, dict) and (r.get("vrp_mw") or 0) > 0)
        filas.append((os.path.basename(a)[:-5], fechas[0] if fechas else "-",
                      fechas[-1] if fechas else "-", len(recs), n_vrp))
    tier = [f for f in filas if f[0] in TIER_A]
    otros = [f for f in filas if f[0] not in TIER_A]
    for f in tier:
        print(f"  {f[0]:22s} primero={f[1][:16]} ultimo={f[2][:16]} n={f[3]} con_vrp>0={f[4]}")
    if otros:
        ult = sorted(f[2] for f in otros if f[2] != "-")
        print(f"  (+{len(otros)} no Tier A; ultimo record entre {ult[0][:10] if ult else '-'} y {ult[-1][:10] if ult else '-'})")
