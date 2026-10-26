# -*- coding: utf-8 -*-
"""Tarea 1.20: huella de los dos techos en el corpus de produccion (origin/main, solo lectura).

(1) M15: el JSON no guarda M15 (A89: no hay campo). Usamos una cota fisica: de noche, en un pixel
    mezcla (lava + fondo) la BT de M13 (4,05 um) es SIEMPRE mayor que la de M15 (10,76 um) por la
    curvatura de Planck; sobre superficie uniforme M15 puede superar a M13 por emisividad a 4 um
    (desierto, hasta ~10 K). Por eso, si `t_max_k` (max M13 de la ROI, que el techo de M15 no toca)
    queda bajo 342,5 - MARGEN, ningun M15 de la ROI pudo llegar al corte. Contamos los records V750
    que NO cumplen esa cota (candidatos) y los anomaly_pixels con bt_k sobre la cota.
(2) I04 NOAA-21: un pixel clampeado al maximo de la LUT (361,00 K) sin el bit de saturacion
    sobreviviria y apareceria como t_max_k ~ 361,0. Contamos records V375 por plataforma con t_max_k
    en bandas altas.
Uso: python -I huella_corpus.py <repo>   (lee con git show origin/main:..., no toca el checkout)
"""
import sys, io, json, subprocess, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
repo = sys.argv[1]
MARGEN = 15.0
COTA15 = 342.5 - MARGEN
files = subprocess.run(["git", "-C", repo, "ls-tree", "--name-only", "origin/main", "data/mirova_equivalent/"],
                       capture_output=True, text=True, check=True).stdout.split()
res = {"cota_m13_k": COTA15, "por_volcan_v750": {}, "v750": collections.Counter(),
       "v375": collections.Counter(), "v375_tmax_top": [], "v750_tmax_top": [], "ventana": [None, None]}
for f in files:
    if not f.endswith(".json"):
        continue
    raw = subprocess.run(["git", "-C", repo, "show", f"origin/main:{f}"], capture_output=True, check=True).stdout
    d = json.loads(raw)
    recs = d["records"] if isinstance(d, dict) else d
    vol = f.split("/")[-1][:-5]
    for r in recs:
        s = str(r.get("sensor", "")); t = r.get("t_max_k"); dt = r.get("datetime_utc")
        if dt:
            lo, hi = res["ventana"]
            res["ventana"] = [dt if lo is None or dt < lo else lo, dt if hi is None or dt > hi else hi]
        if s.endswith("_750"):
            c = res["v750"]; c["records"] += 1
            if t is None: c["sin_tmax"] += 1; continue
            if t >= COTA15: c["tmax_sobre_cota"] += 1
            if t >= 342.5: c["tmax_sobre_342_5"] += 1
            for p in r.get("anomaly_pixels") or []:
                c["pix"] += 1
                if (p.get("bt_k") or 0) >= COTA15: c["pix_sobre_cota"] += 1
            res["v750_tmax_top"].append((t, vol, s, dt))
            pv = res["por_volcan_v750"].setdefault(vol, [0, 0.0]); pv[0] += 1; pv[1] = max(pv[1], t)
        elif s.startswith("VIIRS_") and not s.endswith("_750"):
            c = res["v375"]; plat = s
            c[(plat, "records")] += 1
            if t is None: continue
            for lim in (340.0, 350.0, 360.0, 360.5):
                if t >= lim: c[(plat, f">={lim}")] += 1
            res["v375_tmax_top"].append((t, vol, s, dt))
res["v750_tmax_top"] = sorted(res["v750_tmax_top"], reverse=True)[:10]
res["v375_tmax_top"] = sorted(res["v375_tmax_top"], reverse=True)[:10]
res["v750"] = dict(res["v750"]); res["v375"] = {"|".join(k): v for k, v in res["v375"].items()}
print(json.dumps(res, indent=1, ensure_ascii=False))
json.dump(res, open(__file__.replace(".py", ".json"), "w"), indent=1, ensure_ascii=False)
