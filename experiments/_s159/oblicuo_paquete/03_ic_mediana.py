# -*- coding: utf-8 -*-
"""S159 oblicuo, paso 3: IC 95 % por bootstrap (2000, semilla 159) de la mediana de la razón contra MIROVA por tramo.
Pregunta 1: si el tramo >50 no difiriera de <=25, los intervalos de K se solaparían; el control es que K (déficit
conocido, PR #869) NO se solape y el oráculo SÍ. Pregunta 2: n declarado; n<5 se marca como SIN PODER.
Uso: python 03_ic_mediana.py"""
import csv, json, sys, importlib
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent; sys.path.insert(0, str(AQUI))
M = importlib.import_module("01_razon_por_cenit")
N = AQUI.parent / "n"
obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
tab = {int(r["id"]): r for r in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))}
res = {}
for f in sorted(M.ARTS[0].rglob("resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res: res[r["id"]] = r
inner = M.B.inner_desde_html()
pos = [i for i, o in obj.items() if o["lab"] == "pos" and o["decide"] and (res.get(i) or {}).get("estado") == "ok" and o["clase"] != "diurna"]
rng = np.random.default_rng(159); L = []
for sel_nm, sel in (("todas", lambda v: True), ("sin Chillan", lambda v: v != "NevadosDeChillan"), ("Chillan", lambda v: v == "NevadosDeChillan")):
    for b in ("K", "F", "O"):
        partes = []
        for nm, _, _ in M.TRAMOS:
            xs = []
            for i in pos:
                if not sel(obj[i]["volcan"]) or M.tramo(res[i]["geometria_centro"]["sensor_zenith"]) != nm: continue
                t, m = tab[i], obj[i]["mirova_vrp"]
                if not m: continue
                if b in ("K", "F") and t[f"{b}_pub"] == "True": xs.append(float(t[f"{b}_pc"]) / m)
                if b == "O" and M.alerta_o(res[i]["oraculo"]["geo_linear"], inner[obj[i]["volcan"]]): xs.append(res[i]["oraculo"]["geo_linear"]["vrp_mw"] / m)
            if not xs: partes.append(f"{nm}: SIN DATO"); continue
            xs = np.array(xs); bs = np.median(rng.choice(xs, (2000, len(xs))), axis=1)
            partes.append(f"{nm}: {np.median(xs):.3f} [{np.quantile(bs,.025):.3f}, {np.quantile(bs,.975):.3f}] n={len(xs)}" + (" SIN PODER" if len(xs) < 5 else ""))
        s = f"{sel_nm:12s} {b}  " + " | ".join(partes); print(s); L.append(s)
(AQUI / "03_ic_mediana_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
