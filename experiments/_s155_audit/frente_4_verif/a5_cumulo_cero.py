# -*- coding: utf-8 -*-
"""F4-05 lado MODIS y extension: cumulos 'summit' con magnitud 0,0 (detectados pero invisibles: el exceso sobre
el fondo de anillo recortado a cero, mecanismo de D25) en las mismas pasadas, C0 (tag) contra K (main),
18-sep a 17-oct. Y cuantos de ellos son pasadas con ALERTA de MIROVA (lab pos).
P1: si el recorte no existiera, el conteo pc_vrp==0 con cumulo seria 0 en ambos; si K no cambiara nada, los
   conteos serian iguales. P2: pasadas sin cumulo se cuentan aparte (sin_cumulo), no como cero.
"""
import io, json, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
L = lambda f: [json.loads(x) for x in open(f, encoding="utf-8")]
M = {(r["vol"], r["dt"], r["sensor"]): r for r in L("main_jul_oct.jsonl")}
T = L("tag_c0_ventana.jsonl")
c = collections.Counter(); ej = []
for t in T:
    if t["noche"] > "2026-10-17": continue
    m = M.get((t["vol"], t["dt"], t["sensor"]))
    if m is None: continue
    for nom, r in (("C0", t), ("K", m)):
        if nom == "K" and m["reg"] != "K": continue
        if r["pc_vrp"] is None: c[(nom, r["b"], "sin_cumulo")] += 1; continue
        c[(nom, r["b"], "cumulo")] += 1
        if r["dc"] == "summit" and r["pc_vrp"] == 0:
            c[(nom, r["b"], "summit_0MW")] += 1
            if r.get("lab_SN") == "pos":
                c[(nom, r["b"], "summit_0MW_pos")] += 1
                if nom == "K": ej.append((r["vol"], r["dt"], r["sensor"]))
for k in sorted(c): print(k, c[k])
print("K summit 0 MW con alerta de MIROVA:", ej)
