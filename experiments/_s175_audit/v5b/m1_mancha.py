# -*- coding: utf-8 -*-
"""m1 (V5B): reclasificar con la mancha caliente completa, sin borrarla como sin dato.

Fenomeno: en las laminas VIIRS 750 de Chillan el foco en erupcion es una mancha blanca de varias celdas (saturada en la
paleta). f5b_lib.pixel_mas_claro borra toda componente blanca de 20 px o mas por ser sin dato (l. 118 a 122), asi que
si la mancha es grande borra el foco y elige un pixel del borde. Aqui la mascara de sin dato solo borra componentes que
tocan el borde del panel o de area >= UMBRAL_SIN_DATO; lo demas blanco queda como calor.

Pre-registro (escrito antes de ver el resultado de este script):
  - UMBRAL_SIN_DATO = 400 px (el panel tiene ~22900 px; una mancha de 7x5 celdas V750 son ~180 px).
  - Foco B = componente (8 vecinos) de lum >= max-10 dentro del inner, que contiene el maximo.
  - Control B: alguna celda de la mancha reproduce la Distancia_km desde mirova_center a <= max(tol, 1 celda)
    (el mismo margen que el control del auditor).
  - Clase B: i si la distancia de nuestro punto a la celda MAS CERCANA de la mancha es <= tol; iii si no.
  - Se reporta tambien la clase con el centroide de la mancha.
Pregunta 1: si la mascara no borrara nada, A y B coincidirian (se cuenta). Pregunta 2: si la mascara o el recorte
estuvieran muertos, los conteos de componentes blancas serian 0 o iguales entre sensores. Control positivo: el panel
de 10-10 06:54 V750 tiene una mancha blanca visible y lum_max A 196,7; B tiene que dar lum 255 y >= 20 px.
Denominador: las pasadas con panel de p8_clases.json (aciertos desde 2026-09-22 hasta 2026-11-06, F5 i2_pares).
"""
import json, os, sys, collections
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
F5B = os.path.join(HERE, "..", "f5b")
sys.path.insert(0, F5B)
sys.dont_write_bytecode = True
import f5b_lib as L
import yaml
sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
UMBRAL_SIN_DATO = 400
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
ARCH = {"NevadosDeChillan": "ChillanNevadosde"}
refs = json.load(open(os.path.join(F5B, "p6_tif_referencia_out.json"), encoding="utf-8"))
recs = [x for x in json.load(open(os.path.join(F5B, "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
gr = {}


def grilla(vol, b):
    if (vol, b) not in gr:
        ref = refs[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
        g = L.grilla(os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"])))
        g["mc"] = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        g["inner"] = L.mascara_inner(g, g["mc"], V[vol]["inner_radius_km"])
        g["celda_km"] = abs(g["transform"].e) * 111.0
        gr[(vol, b)] = g
    return gr[(vol, b)]


def analizar(x):
    vol, b = x["vol"], x["b"]
    g = grilla(vol, b)
    n = g["n"]
    fn = os.path.join(TMP, "png", x["png"].split("/")[-2] + "_" + os.path.basename(x["png"]))
    im = L.abrir_png(fn)
    bb = L.bbox_marco(im, x["panel"])
    X0, Y0, W, Hh = L.geometria(bb)
    pan, px_x, px_y = L.recorte(im, X0, Y0, W, Hh)
    Lu = pan.astype(float).mean(axis=2)
    cy, cx = L.celdas_de(px_x, px_y, X0, Y0, W, Hh, n)
    inner_p = g["inner"][np.ix_(cy, cx)]
    bl = pan.min(axis=2) > 245
    lab, nl = ndimage.label(bl)
    sin_dato = np.zeros(bl.shape, bool)
    borr = 0
    areas_inner = []
    areas_todas = []
    for i in range(1, nl + 1):
        m = lab == i
        a = int(m.sum())
        toca = m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()
        areas_todas.append((a, bool(toca)))
        if toca or a >= UMBRAL_SIN_DATO:
            sin_dato |= m
        elif (m & inner_p).any():
            areas_inner.append(a)
            if a >= 20:
                borr += 1   # componente que A borra por sin dato y B conserva
    sin_dato = ndimage.binary_dilation(sin_dato, iterations=1)
    Lm = np.where(inner_p & ~sin_dato, Lu, -1.0)
    if Lm.max() < 0:
        return None
    py, px = np.unravel_index(np.argmax(Lm), Lm.shape)
    cand = Lm >= Lm.max() - 10
    lab2, _ = ndimage.label(cand, structure=np.ones((3, 3)))
    man = lab2 == lab2[py, px]
    rr = cy[np.where(man)[0]]
    cc = cx[np.where(man)[1]]
    celdas = sorted(set(zip(rr.tolist(), cc.tolist())))
    d_mc = [L.hav(g["lats"][r, c], g["lons"][r, c], *g["mc"]) for r, c in celdas]
    la, lo = float(x["our_lat"]), float(x["our_lon"])
    d_ours = [L.hav(g["lats"][r, c], g["lons"][r, c], la, lo) for r, c in celdas]
    pyc, pxc = ndimage.center_of_mass(man)
    ri = int(np.clip((px_y[0] + pyc + 0.5 - Y0) / Hh * n, 0, n - 1))
    ci = int(np.clip((px_x[0] + pxc + 0.5 - X0) / W * n, 0, n - 1))
    dcent = L.hav(g["lats"][ri, ci], g["lons"][ri, ci], la, lo)
    tol = L.TOL[b]
    tolc = max(tol, g["celda_km"])
    dist = x.get("dist_tabla_km")
    tiene = dist not in (None, "")
    idx = int(np.argmin([abs(d - dist) for d in d_mc])) if tiene else None
    return dict(vol=vol, b=b, sensor=x["sensor"], dt=x["dt"], vrp=x["vrp_mirova"], prot=x["protegida"], dist_tabla=dist, fuente=x.get("fuente_dist"),
                claseA=x["clase"], controlA=x.get("control_distancia"), d_A_ours=x.get("d_png_nuestro_km"), lum_A=x.get("lum_max"), lum_B=float(Lm.max()),
                n_celdas=len(celdas), man_px=int(man.sum()), areas_blanco_inner=areas_inner, comps_borradas_por_A=borr, areas_todas=areas_todas,
                d_mc_min=round(min(d_mc), 3), d_mc_max=round(max(d_mc), 3),
                ctrl_B=(any(abs(d - dist) <= tolc for d in d_mc) if tiene else None),
                ctrl_B_1cel=(any(abs(d - dist) <= g["celda_km"] for d in d_mc) if tiene else None),
                d_B_ours_min=round(min(d_ours), 3), d_B_ours_max=round(max(d_ours), 3), d_B_ours_cent=round(dcent, 3),
                d_ours_celda_tabla=(round(d_ours[idx], 3) if tiene else None),
                tol=tol, celda_km=round(g["celda_km"], 3), panel=x["panel"], png=x["png"], etiqueta=x.get("etiqueta_panel"),
                celdas=celdas if len(celdas) <= 40 else celdas[:40])


out = []
for x in recs:
    if "png" not in x or x.get("png") in (None, ""):
        continue
    try:
        o = analizar(x)
    except Exception as e:
        print("ERROR", x["vol"], x["b"], x["dt"], repr(e))
        continue
    if o:
        out.append(o)
json.dump(out, open(os.path.join(HERE, "m1_mancha.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("con panel analizados:", len(out))
print("componentes blancas interiores (no tocan borde) en todo el panel, por area, histograma:")
hist = collections.Counter()
for o in out:
    for a, toca in o["areas_todas"]:
        if not toca:
            hist[min(a // 50 * 50, 2000)] += 1
print(sorted(hist.items()))
print("records donde A borro una componente blanca de calor (>=20 px, no toca borde, <400 px, en inner):", sum(o["comps_borradas_por_A"] > 0 for o in out), "de", len(out))
print(collections.Counter((o["vol"], o["b"]) for o in out if o["comps_borradas_por_A"] > 0))
print("A != B en pixel elegido (lum distinta):", sum(1 for o in out if o["lum_A"] is not None and abs(o["lum_A"] - o["lum_B"]) > 0.5))
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    g = [o for o in out if o["b"] == b]
    a = sum(1 for o in g if o["controlA"] is True)
    bb = sum(1 for o in g if o["ctrl_B"] is True)
    c = sum(1 for o in g if o["ctrl_B_1cel"] is True)
    print(f"{b}: n={len(g)} control A ok {a}, control B (cualquier celda de la mancha, misma tolerancia) ok {bb}, B a 1 celda {c}")
ch = [o for o in out if o["vol"] == "NevadosDeChillan"]
print("Chillan:")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    g = [o for o in ch if o["b"] == b]
    print(b, "n", len(g), "ctrlA", sum(1 for o in g if o["controlA"] is True), "ctrlB", sum(1 for o in g if o["ctrl_B"] is True), "ctrlB1c", sum(1 for o in g if o["ctrl_B_1cel"] is True),
          "n_celdas p50", float(np.median([o["n_celdas"] for o in g])), "max", max(o["n_celdas"] for o in g),
          "d_B_ours_min<=tol", sum(1 for o in g if o["d_B_ours_min"] <= o["tol"]),
          "d_B_cent<=tol", sum(1 for o in g if o["d_B_ours_cent"] <= o["tol"]))
print("Los de la afirmacion 351 y vecinos clase A iii VIIRS Chillan:")
for o in ch:
    if (o["claseA"].startswith("iii") and o["b"] != "MODIS") or (o["dt"] == "2026-10-18 06:00" and o["b"] == "VIIRS375"):
        print({k: o[k] for k in ("sensor", "dt", "vrp", "prot", "dist_tabla", "claseA", "lum_A", "lum_B", "d_A_ours", "n_celdas", "man_px", "areas_blanco_inner", "comps_borradas_por_A", "d_mc_min", "d_mc_max", "ctrl_B", "ctrl_B_1cel", "d_B_ours_min", "d_B_ours_max", "d_B_ours_cent", "d_ours_celda_tabla")})
