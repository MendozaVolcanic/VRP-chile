# -*- coding: utf-8 -*-
"""V-16: ubica la mascara de alerta de la Fig. A2 (p. 19) midiendo pixeles blancos en el panel ALERT Mask.
(1) Si lo que mide estuviera roto, fallaria? Control: el mismo procedimiento sobre la Fig. A3 (Erta Ale), cuya
    mascara debe caer en la celda central 26,26. (2) Instrumento muerto: si no hay blancos imprime n=0."""
import fitz, numpy as np, math
d = fitz.open("../../../documentacion/sp426.5.pdf")
pix = d[18].get_pixmap(dpi=200)
a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(int)
def panel(y0, y1, x0=540, x1=770):
    sub = a[y0:y1, x0:x1]
    negro = (sub.sum(2) < 60)
    # caja negra = filas y columnas con mayoria de negro (descarta rotulos de ejes)
    filas = np.where(negro.sum(1) > 150)[0]; cols = np.where(negro.sum(0) > 150)[0]
    bx0, bx1, by0, by1 = cols.min(), cols.max(), filas.min(), filas.max()
    blanco = (sub.min(2) > 200)
    blanco[:, :bx0] = False; blanco[:, bx1:] = False; blanco[:by0] = False; blanco[by1:] = False
    wy, wx = np.where(blanco)
    w = (bx1 - bx0 + 1) / 51.0; h = (by1 - by0 + 1) / 51.0
    cx = (wx.mean() - bx0) / w + 0.5; cy = (by1 - wy.mean()) / h + 0.5
    print(" caja px", bx0, bx1, by0, by1, "celda px", round(w, 2), round(h, 2), "n blancos", len(wx))
    print(" celdas x", round((wx.min()-bx0)/w+0.5,1), "a", round((wx.max()-bx0)/w+0.5,1), " y", round((by1-wy.max())/h+0.5,1), "a", round((by1-wy.min())/h+0.5,1))
    dx, dy = cx - 26, cy - 26
    print(" centroide celda", round(cx, 2), round(cy, 2), "-> dx km", round(dx, 2), "dy km", round(dy, 2), "dist", round(math.hypot(dx, dy), 2), "rumbo", round(math.degrees(math.atan2(dx, dy)) % 360, 1))
print("A2 ALERT mask"); panel(500, 740)
print("A3 ALERT mask (control, esperado centro)"); panel(1400, 1640)
