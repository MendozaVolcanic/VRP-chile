# -*- coding: utf-8 -*-
"""Tarea 1.20 (1), dos cotas sobre el corpus:
 a) VRP minimo por pixel (metodo MIR del pipeline) al que M15 PUEDE llegar a 342,5 K, sobre todo T_h:
    el minimo es el pixel uniforme a 342,5 K (cualquier componente mas caliente da mas MIR por igual TIR).
 b) M15 implicito del pixel mas caliente de los records V750 con t_max_k >= 327,5 K: si el pixel de
    nti_max es el de t_max, L15 = L13 (1 - NTI)/(1 + NTI). Supuesto declarado, no medido.
 c) VRP maximo por pixel en anomaly_pixels de todo V750 del corpus.
Uso: python -I cota_vrp_y_m15_implicito.py <repo>
"""
import sys, io, json, subprocess
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C1, C2 = 1.191042e8, 14388.0
L13, L15 = 4.050, 10.763
def L(T, lam): return C1 / (lam**5 * (np.exp(C2 / (lam * T)) - 1.0))
def BT(Lv, lam): return C2 / (lam * np.log(C1 / (Lv * lam**5) + 1.0))
K = 19.7 * 562500.0
out = {"a_vrp_min_mw_por_tbg": {}}
for tbg in (250, 270, 290):
    out["a_vrp_min_mw_por_tbg"][tbg] = round(float(K * (L(342.5, L13) - L(tbg, L13)) / 1e6), 1)
repo = sys.argv[1]
files = subprocess.run(["git", "-C", repo, "ls-tree", "--name-only", "origin/main", "data/mirova_equivalent/"],
                       capture_output=True, text=True, check=True).stdout.split()
maxpix = (0.0, None); implic = []
for f in files:
    d = json.loads(subprocess.run(["git", "-C", repo, "show", f"origin/main:{f}"], capture_output=True, check=True).stdout)
    for r in d["records"]:
        if not str(r.get("sensor", "")).endswith("_750"):
            continue
        for p in r.get("anomaly_pixels") or []:
            v = p.get("vrp_mw") or 0.0
            if v > maxpix[0]:
                maxpix = (v, [f.split("/")[-1], r["sensor"], r["datetime_utc"], p.get("bt_k"), p.get("dist_km")])
        t, n = r.get("t_max_k"), r.get("nti_max")
        if t is not None and t >= 327.5 and n is not None:
            l13 = L(t, L13); l15 = l13 * (1 - n) / (1 + n)
            implic.append([f.split("/")[-1], r["sensor"], r["datetime_utc"], t, n, round(float(BT(l15, L15)), 2)])
out["b_m15_implicito"] = implic
out["c_vrp_max_pixel_v750"] = maxpix
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1, ensure_ascii=False)
