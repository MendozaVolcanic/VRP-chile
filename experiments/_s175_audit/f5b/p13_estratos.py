# -*- coding: utf-8 -*-
"""P13 (F5b): estratos de p8_clases.json para leer bien los (iv) y los (iii).

Por qué: el control de distancia (el píxel más claro tiene que reproducir la Distancia_km de la tabla a ± max(tol, 1
celda)) cae en 108 de 305, muchas veces por poco (0,02 km medido contra 0,84 de tabla en Chillán VIIRS 375). La tabla
de MIROVA da distancias cuantizadas por la grilla (sqrt(i^2 + j^2) por celda), así que un fallo por menos de una celda
extra no es «otro foco», es el borde del control. Acá se separa: (iv) por cuánto falla el control (en celdas) y a qué
distancia queda el píxel de nuestro punto; (iii) por prominencia del píxel elegido (lum max menos p99 del panel: si es
negativa, el píxel no destaca y la elección es débil); marcos grises (sesgo de ~1 px en el centro de línea); tamaño de
la mancha saturada en Chillán. También se mide si las distancias de la tabla son múltiplos de la grilla (control de que
la cuantización existe). Sólo lee. Salida: p13_estratos.out.txt.
"""
import collections, json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
o = [x for x in json.load(open(os.path.join(H, "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
CELDA = {"VIIRS375": 0.374, "VIIRS750": 0.747, "MODIS": 0.991}   # km, de p7 (celda_km_aprox = |e| * 111)

print("== (iv) por control fallido: cuánto falla, en celdas, y d_png_nuestro ==")
fall = [x for x in o if x["clase"] == "iv" and x.get("control_distancia") is False]
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    g = [x for x in fall if x["b"] == b]
    if not g:
        continue
    dif = np.array([abs(x["d_png_mirova_center_km"] - x["dist_tabla_km"]) / CELDA[b] for x in g])
    dn = np.array([x["d_png_nuestro_km"] for x in g])
    tol = g[0]["tol_km"]
    print(f"{b}: n={len(g)}; falla por <= 1 celda extra (|d - tabla| <= tol + 1 celda): {(dif * CELDA[b] <= tol + CELDA[b]).sum()}; "
          f"por > 3 celdas: {(dif > 3).sum()}; d_png_nuestro <= tol en {(dn <= tol).sum()} de {len(g)}; "
          f"ambos (falla <= 1 celda extra y d_nuestro <= tol): {((dif * CELDA[b] <= tol + CELDA[b]) & (dn <= tol)).sum()}")
    for vol in sorted({x["vol"] for x in g}):
        gg = [x for x in g if x["vol"] == vol]
        d2 = np.array([abs(x["d_png_mirova_center_km"] - x["dist_tabla_km"]) for x in gg])
        dn2 = np.array([x["d_png_nuestro_km"] for x in gg])
        pr = np.array([x["prominencia"] for x in gg])
        print(f"   {vol}: n={len(gg)}; |d - tabla| p50 {np.median(d2):.2f} max {d2.max():.2f} km; d_nuestro p50 {np.median(dn2):.2f} max {dn2.max():.2f}; "
              f"prominencia < 0: {(pr < 0).sum()}; protegidas {sum(1 for x in gg if x.get('protegida') == 'True')}")

print("\n== (iii) por prominencia ==")
for x in sorted([x for x in o if x["clase"].startswith("iii")], key=lambda x: -x["prominencia"]):
    print(f"   {x['vol']:20s} {x['sensor']:16s} {x['dt']} {float(x['vrp_mirova']):6.2f} MW prot={x['protegida']:5s} prom={x['prominencia']:6.1f} mancha={x['mancha_px']:3d} "
          f"d_nuestro={x['d_png_nuestro_km']:5.2f} tabla={x['dist_tabla_km']} d_mc={x['d_png_mirova_center_km']} fuente={x['fuente_dist']} panel={x['panel']}")

print("\n== marcos grises entre los aciertos con panel ==", collections.Counter((x["b"], x.get("marco_verde")) for x in o if "marco_verde" in x))
print("== mancha saturada (px) en Chillán por sensor (p50, p90, max) ==")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    m = [x["mancha_px"] for x in o if x["vol"] == "NevadosDeChillan" and x["b"] == b and "mancha_px" in x]
    print(f"   {b}: n={len(m)} p50 {np.median(m):.0f} p90 {np.percentile(m, 90):.0f} max {max(m)}")
print("== prominencia < 0 entre (i) por sensor ==", collections.Counter((x["b"], x["prominencia"] < 0) for x in o if x["clase"].startswith("i") and not x["clase"].startswith("iii") and "prominencia" in x))

print("\n== ¿las distancias de la tabla son múltiplos de la grilla? (|dist - sqrt(i^2+j^2)*celda| <= 0,03 km, i,j <= 60) ==")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    ds = sorted({x["dist_tabla_km"] for x in o if x["b"] == b and x.get("dist_tabla_km") and x["fuente_dist"] == "CONS"})
    c = CELDA[b]
    mult = [d for d in ds if any(abs(d - np.hypot(i, j) * c) <= 0.03 for i in range(61) for j in range(i, 61))]
    print(f"   {b}: {len(mult)} de {len(ds)} valores distintos de la tabla caen en la grilla; valores: {ds[:14]}")
print("\n== lag de la lámina (h) por sensor ==", {b: [round(float(v), 1) for v in np.percentile([x['lag_lamina_h'] for x in o if x['b'] == b and 'lag_lamina_h' in x], [50, 90, 100])] for b in ("VIIRS375", "VIIRS750", "MODIS")})
