# -*- coding: utf-8 -*-
"""Baja una muestra de Dist.png archivadas (mirova-tif-archive, por raw, sin clone).
Por volcan y sensor: la primera captura de cada bloque de PASO dias (md5 unico). Uso:
python bajar_dist.py index_png.csv carpeta_destino sensor paso_dias"""
import sys, os, urllib.request, pandas as pd
idx, dest, sensor, paso = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
d = pd.read_csv(idx)
d = d[(d.kind == "Dist") & (d.sensor == sensor)].drop_duplicates("md5").copy()
d["t"] = pd.to_datetime(d.last_modified_utc)
sel = []
for v, g in d.groupby("volcano"):
    g = g.sort_values("t"); t0 = g.t.min(); k = -1
    for r in g.itertuples():
        b = int((r.t - t0).total_seconds() // (paso * 86400))
        if b != k:
            sel.append(r); k = b
out = []
for r in sel:
    loc = os.path.join(dest, r.png_path.replace("/", "_"))
    if not os.path.exists(loc):
        try:
            urllib.request.urlretrieve("https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/" + r.png_path, loc)
        except Exception as e:
            print("fallo", r.png_path, e); continue
    out.append({"volcano": r.volcano, "sensor": sensor, "last_modified_utc": r.last_modified_utc, "md5": r.md5, "archivo": loc})
pd.DataFrame(out).to_csv(os.path.join(dest, f"muestra_{sensor}.csv"), index=False)
print("bajadas", len(out))
