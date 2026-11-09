# -*- coding: utf-8 -*-
"""V177 v04: recortes ampliados de paneles (a lo que entra por el ojo), con el contorno del inner, nuestro punto (cian) y centroide de C2 (magenta)."""
import os, sys, pickle
import numpy as np
from PIL import Image, ImageDraw
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *

R = pickle.load(open(os.path.join(HERE, "v01_manchas.pkl"), "rb"))
os.makedirs(os.path.join(HERE, "crops"), exist_ok=True)
CASOS = [(CH, "VIIRS_NOAA20_750", "2026-10-10 06:54", "cambia_v750_1010"), (CH, "VIIRS_NOAA21_750", "2026-10-27 05:36", "cambia_v750_1027"), (CH, "MODIS_TERRA", "2026-10-16 01:40", "cambia_modis_1016"),
         (CH, "VIIRS_NOAA21", "2026-10-18 05:06", "v375_1018")]
Sinm = [o for o in R if o["vol"] == CH and o["b"] == "VIIRS375" and not o["C2"]["sat"]]
CASOS.append((CH, Sinm[3]["sensor"], Sinm[3]["dt"], "control_sin_mancha"))
Cau = [o for o in R if o["vol"] == "PuyehueCordonCaulle" and o["b"] == "VIIRS750" and o["C1"]["px"] >= 20]
if Cau:
    CASOS.append(("PuyehueCordonCaulle", Cau[0]["sensor"], Cau[0]["dt"], "caulle_v750"))
ESC = 8
tiles = []
for vol, sen, d, nom in CASOS:
    o = next(x for x in R if x["vol"] == vol and x["sensor"] == sen and x["dt"] == d)
    g = grilla(vol, o["b"])
    P = panel(o["x"], g)
    cels = np.where(P["inn"])
    y0, y1, x0, x1 = cels[0].min(), cels[0].max(), cels[1].min(), cels[1].max()
    a = P["a"][max(0, y0 - 8):y1 + 9, max(0, x0 - 8):x1 + 9]
    y0_, x0_ = max(0, y0 - 8), max(0, x0 - 8)
    im = Image.fromarray(a).resize((a.shape[1] * ESC, a.shape[0] * ESC), Image.NEAREST).convert("RGB")
    dr = ImageDraw.Draw(im)
    def xy(la, lo):
        dd = hav(g["lats"], g["lons"], la, lo)
        r, c = np.unravel_index(np.argmin(dd), dd.shape)
        px = (c + 0.5) / P["n"] * P["W"] + P["X0"] - P["px"][0] - x0_
        py = (r + 0.5) / P["n"] * P["H"] + P["Y0"] - P["py"][0] - y0_
        return px * ESC, py * ESC
    x_, y_ = xy(*o["pt"])
    dr.ellipse([x_ - 6, y_ - 6, x_ + 6, y_ + 6], outline=(0, 255, 255), width=2)
    x_, y_ = xy(o["C2"]["la"], o["C2"]["lo"])
    dr.ellipse([x_ - 9, y_ - 9, x_ + 9, y_ + 9], outline=(255, 0, 255), width=2)
    x_, y_ = xy(o["A"]["la"], o["A"]["lo"])
    dr.rectangle([x_ - 7, y_ - 7, x_ + 7, y_ + 7], outline=(255, 160, 0), width=2)
    dr.text((4, 4), f"{nom} {sen} {d} VRP {o['vrp']} F5b {o['claseF5b']}", fill=(255, 255, 0))
    im.save(os.path.join(HERE, "crops", nom + ".png"))
    tiles.append(im)
    print(nom, o["vol"], sen, d, im.size, "sat", o["C2"]["sat"], "mx", o["C2"]["mx"], "celdas", o["C2"]["nc"], "px", o["C2"]["px"])
W = sum(t.size[0] for t in tiles[:3]) + 20
H = max(t.size[1] for t in tiles[:3]) + max(t.size[1] for t in tiles[3:]) + 10
m = Image.new("RGB", (max(W, sum(t.size[0] for t in tiles[3:]) + 20), H), (60, 0, 0))
x = 0
for t in tiles[:3]:
    m.paste(t, (x, 0))
    x += t.size[0] + 10
x = 0
y = max(t.size[1] for t in tiles[:3]) + 10
for t in tiles[3:]:
    m.paste(t, (x, y))
    x += t.size[0] + 10
m.save(os.path.join(HERE, "crops", "mosaico.png"))
print(m.size)
