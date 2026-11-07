# -*- coding: utf-8 -*-
"""F3 S175, item I1: la via «codigo MIROVA» en MODIS de produccion, contra los records de 752d348bc.
P1: si la via estuviera apagada, veria 0 records via_codigo_mirova despues del corte (lo distingue). P2: denominador
= records MODIS de los 11 Tier A; con 0 records el veredicto es SIN DATO. Control positivo: antes del 2026-11-02 todo
MODIS debe salir sin la clave (K)."""
import io, json, subprocess, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C = sys.argv[1] if len(sys.argv) > 1 else "752d348bc"
T = ["Lascar","Lastarria","Isluga","NevadosDeChillan","Llaima","Villarrica","Chaiten","Tupungatito","PlanchonPeteroa","Copahue","PuyehueCordonCaulle"]
res = {}; despues_k = []; diag = collections.Counter(); src = collections.Counter(); antes = collections.Counter()
for v in T:
    d = json.loads(subprocess.run(["git","show",f"{C}:data/mirova_equivalent/{v}.json"],capture_output=True).stdout)
    for r in d["records"]:
        if not str(r.get("sensor","")).startswith("MODIS"): continue
        dt = r.get("datetime_utc",""); via = r.get("via_codigo_mirova")
        if dt < "2026-11-02T18": antes[repr(via)] += 1; continue
        k = "via" if via is True else repr(via)
        res[k] = res.get(k,0)+1
        dg = r.get("diag_codigo_mirova")
        if via is not True:
            despues_k.append((v, dt, r.get("sensor"), repr(via), json.dumps(dg)[:200] if dg is not None else None, r.get("processed_utc")))
        if isinstance(dg, dict):
            for kk in dg: diag[kk] += 1
        src[r.get("final_hotspot_source")] += 1
print("commit", C)
print("MODIS antes del 2026-11-02T18 por valor de via_codigo_mirova:", dict(antes))
print("MODIS desde 2026-11-02T18 por via:", res)
print("final_hotspot_source desde el corte:", dict(src))
print("claves de diag_codigo_mirova:", dict(diag))
print("records MODIS desde el corte que NO son de la via:", len(despues_k))
for x in despues_k[:40]: print("  ", x)
