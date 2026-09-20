# -*- coding: utf-8 -*-
"""V-16: condicion 2 de la regla general aplicada a ciegas: distancia de la mascara ALERT al centro de grilla en
las figuras A1..A9 (paginas 18-22). Detecta paneles negros grandes automaticamente (el panel ALERT Mask es el unico
de fondo negro puro en la fila inferior, columna central).
(1) roto? control: los negativos (A4,A7,A9) deben dar n blancos = 0. (2) muerto? imprime n blancos por figura."""
import fitz, numpy as np, math
d = fitz.open("../../../documentacion/sp426.5.pdf")
for pg in range(17, 23):
    pix = d[pg].get_pixmap(dpi=200)
    a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(int)
    t = d[pg].get_text()
    figs = [l[:40] for l in t.split("\n") if l.startswith("Fig. A")]
    col = a[:, 540:770]
    negro = col.sum(2) < 60
    filas = negro.sum(1) > 150
    # segmentos verticales contiguos
    segs = []; ini = None
    for y, f in enumerate(filas):
        if f and ini is None: ini = y
        if not f and ini is not None:
            if y - ini > 150: segs.append((ini, y - 1))
            ini = None
    print("pag", pg + 1, figs, "paneles negros en columna central:", segs)
    for (y0, y1) in segs:
        sub = col[y0:y1 + 1]
        cols = np.where((sub.sum(2) < 60).sum(0) > 150)[0]
        x0, x1 = cols.min(), cols.max()
        s2 = sub[:, x0:x1 + 1]
        bl = s2.min(2) > 200
        wy, wx = np.where(bl)
        if len(wx) == 0: print("   panel", y0, y1, "n blancos 0 (sin mascara)"); continue
        w = (x1 - x0 + 1) / 51; h = (y1 - y0 + 1) / 51
        cx = wx.mean() / w + 0.5; cy = (y1 - y0 - wy.mean()) / h + 0.5
        print("   panel", y0, y1, "n blancos", len(wx), "centroide celda", round(cx, 1), round(cy, 1), "dist km", round(math.hypot(cx - 26, cy - 26), 2), "rumbo", round(math.degrees(math.atan2(cx - 26, cy - 26)) % 360))
