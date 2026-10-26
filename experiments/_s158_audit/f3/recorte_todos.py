# -*- coding: utf-8 -*-
"""F3: cuántas pasadas con detección quedan en 0,0 MW porque TODOS sus alertados tienen ΔL recortado a 0 (fondo de
anillo >= L_hot), por volcán y sensor. Ventana: 2026-03-01 a 2026-10-20, noche (03-09 UTC), los 11 Tier A.
Es la cara medible del fondo escalar de anillo contra el fondo local de MIROVA (código V750: interpolado, sin recorte).
Instrumento: un record con n_anomalous_pixels = 0 no entra (no es FALLA de magnitud, es no detección). Control
positivo: los volcanes con kernel local en V375 (Villarrica, PCC, Chaitén, PP, Lastarria) deberían tener menos
recorte en V375 que en V750, donde no hay kernel. Denominador: pasadas nocturnas con >= 1 alertado.
Uso: python -B recorte_todos.py <raiz>
"""
import json, os, sys
import pandas as pd
ROOT = sys.argv[1]
V = ["Villarrica", "Lascar", "Tupungatito", "PuyehueCordonCaulle", "Llaima", "Copahue", "NevadosDeChillan",
     "PlanchonPeteroa", "Isluga", "Lastarria", "Chaiten"]
def bucket(x):
    x = str(x or "").upper()
    return ("V750" if "750" in x else "V375") if "VIIRS" in x else "MODIS"
rows = []
for v in V:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{v}.json"), encoding="utf-8"))
    for r in d["records"]:
        t = str(r["datetime_utc"])
        if t < "2026-03-01" or t > "2026-10-21" or not (3 <= int(t[11:13]) <= 9):
            continue
        n = r.get("n_anomalous_pixels") or 0
        px = r.get("anomaly_pixels") or []
        if n == 0 or not px:
            continue
        pc = r.get("primary_cluster") or {}
        rows.append({"vol": v, "b": bucket(r.get("sensor")), "todo_rec": all(p["vrp_mw"] <= 0 for p in px) and len(px) == n,
                     "pc0": (pc.get("vrp_mw") or 0) <= 0, "summit": r.get("distance_class") == "summit"})
D = pd.DataFrame(rows)
T = D.groupby(["vol", "b"]).agg(n=("pc0", "size"), todo_recortado=("todo_rec", "sum"), cumulo_0MW=("pc0", "sum"),
                                summit=("summit", "sum"), summit_y_recortado=("todo_rec", lambda x: int((x & D.loc[x.index, "summit"]).sum())))
T["%recortado"] = (100 * T.todo_recortado / T.n).round(1)
print(T.unstack("b").swaplevel(axis=1).sort_index(axis=1).to_string())
