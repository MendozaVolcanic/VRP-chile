# -*- coding: utf-8 -*-
"""Verificador. Lee UNA vez todas las Dist.png de la muestra VIIRS 375 del estudio (y las VIIRS 750 de dist_sg)
con el lector del propio estudio (dist_png.leer, sin modificar) y guarda las lecturas en un pickle.
Uso: python leer_todo.py <carpeta_estudio> <salida.pkl>"""
import sys, os, pickle, glob
EST, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(EST, "scripts"))
import dist_png as D
import pandas as pd

mu = pd.read_csv(os.path.join(EST, "datos/dist375/muestra_VIIRS375.csv"))
res = {}
for r in mu.itertuples():
    p = os.path.join(EST, r.archivo.replace("\\", "/"))
    res[os.path.basename(p)] = {"volcano": r.volcano, "sensor": "VIIRS375", "lm": r.last_modified_utc, "lect": D.leer(p)}
for p in glob.glob(os.path.join(EST, "datos/dist_sg/*.png")):
    b = os.path.basename(p)
    if b in res:
        continue
    parts = b.replace("data_png_", "").split("_")
    vol, fecha, hora, sensor = parts[0], parts[1], parts[2], parts[3]
    lm = pd.Timestamp(f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:]} {hora[:2]}:{hora[2:4]}:{hora[4:]}")
    res[b] = {"volcano": vol, "sensor": sensor, "lm": str(lm), "lect": D.leer(p), "solo_nombre_lm": True}
pickle.dump(res, open(OUT, "wb"))
print("lecturas", len(res), "sin geometria", sum(v["lect"] is None for v in res.values()))
