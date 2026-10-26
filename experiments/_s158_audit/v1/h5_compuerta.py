# -*- coding: utf-8 -*-
"""V1 (S158) F1-H5: de los publicados V750 en K con primer pase vacio (diag_n_first_pass_pixels == 0), cuantos tienen
TODOS sus pixeles alertados con bt <= t_bg + 3 K (o sea, la compuerta de detection_context.py:546 los bloquea por
construccion). Control positivo: en los publicados con primer pase no vacio, algun pixel debe superar t_bg + 3 K
(si no, el instrumento no distingue). Ventana >= 2026-09-18; insumo v1/h3_caja.csv (predicado del tablero con node)."""
import json, pandas as pd, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pd.read_csv("experiments/_s158_audit/v1/h3_caja.csv")
out = []
for vol, g in R.groupby("v"):
    d = json.load(open(f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    idx = {(r["datetime_utc"], r["sensor"]): r for r in d["records"]}
    for _, p in g.iterrows():
        r = idx[(p.t, p.s)]
        bts = [q["bt_k"] for q in r.get("anomaly_pixels") or []]
        tb = r["t_bg_k"]
        out.append(dict(v=vol, t=p.t, fp=p.fp, sp=p.sp, t_bg=tb, bt_max_px=max(bts), n_sobre=sum(b > tb + 3 for b in bts), n=len(bts)))
O = pd.DataFrame(out)
for nm, s in [("primer pase vacio", O.fp == 0), ("primer pase no vacio", O.fp > 0)]:
    x = O[s]
    print(nm, len(x), "| con 0 pixeles sobre t_bg+3K:", int((x.n_sobre == 0).sum()), "| mediana bt_max - t_bg:", round((x.bt_max_px - x.t_bg).median(), 2))
print(O[O.fp == 0].to_string(index=False))
