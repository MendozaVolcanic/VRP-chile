# -*- coding: utf-8 -*-
"""V177 v06. Pregunta: la regla B puede guardar como mancha un hueco de sin dato chico? Lo unico que lo arbitra es el NaN del TIF de la misma pasada.

Fenomeno: blanco = saturacion o sin dato. Con TIF de la pasada (antes del 22-sep), sabemos que celdas son NaN. Si hay componentes blancas de 20 a 399 px, sin tocar el borde, que son NaN en el TIF, B las guarda como calor: falso.
Datos: pares TIF y lamina de V5B m2 (etiqueta nuevo y auditor), copia en s175_audit\\v5b\\m2.
Pre-registro: se cuentan, por componente blanca: area, toca borde, fraccion de celdas con NaN en el TIF, y si esta en el inner. Se reporta la tabla area x NaN.
Control: las componentes >= 400 o que tocan borde deben ser NaN casi siempre (si no, el pareo o la geometria estan mal).
"""
import json, os, sys, collections
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *
import importlib.util
spec = importlib.util.spec_from_file_location("f5b_lib", F + r"\orig\f5b_lib.py")
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
import rasterio
V5 = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5b\m2_validacion.json"
M = BASE + r"\s175_audit\v5b\m2"
cases = json.load(open(V5, encoding="utf-8"))
tab = collections.Counter()
det = []
n_casos = 0
omit = collections.Counter()
for c in cases:
    if not c.get("ocr_ok") or c.get("panel") is None or not c.get("tif") or not c.get("png"):
        omit["sin ocr/panel"] += 1
        continue
    t = os.path.join(M, "tif", c["tif"].split("/")[-2] + "_" + os.path.basename(c["tif"]))
    p = os.path.join(M, "png", c["png"].split("/")[-2] + "_" + os.path.basename(c["png"]))
    if not (os.path.exists(t) and os.path.exists(p)):
        omit["sin archivo"] += 1
        continue
    with rasterio.open(t) as ds:
        a = ds.read(1).astype(float)
        if ds.nodata is not None:
            a[a == ds.nodata] = np.nan
    im = L.abrir_png(p)
    bb = L.bbox_marco(im, c["panel"])
    if bb is None:
        omit["sin marco"] += 1
        continue
    X0, Y0, W, H = L.geometria(bb)
    pan, px, py = L.recorte(im, X0, Y0, W, H)
    n = a.shape[0]
    cy, cx = L.celdas_de(px, py, X0, Y0, W, H, n)
    nanp = np.isnan(a)[np.ix_(cy, cx)]
    P = dict(a=pan, L=pan.astype(float).mean(axis=2))
    n_casos += 1
    for w in blancas(P):
        f = float(nanp[w["mask"]].mean())
        cat = "toca o >=400" if (w["toca"] or w["area"] >= 400) else ("20 a 399" if w["area"] >= 20 else "<20")
        tab[(cat, "NaN>=0,5" if f >= 0.5 else "NaN<0,5")] += 1
        if cat != "toca o >=400" and f >= 0.5:
            det.append((c["vol"], c["b"], c["dt"], w["area"], round(f, 2)))
print("casos con par TIF y lamina:", n_casos, "omitidos", dict(omit))
for k in sorted(tab):
    print("  ", k, tab[k])
print("componentes chicas que son NaN en el TIF (B las guardaria):", det[:30], "total", len(det))
print("pares por volcan y sensor:", collections.Counter((c["vol"], c["b"]) for c in cases if c.get("ocr_ok")).most_common(12))
print("incluye Chillan:", any(c["vol"] == CH for c in cases))
