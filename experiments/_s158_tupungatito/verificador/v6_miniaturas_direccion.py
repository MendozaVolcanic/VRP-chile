# -*- coding: utf-8 -*-
"""Verificador S158. Vía independiente de la serie «Last Month»: la miniatura de la pasada en el panel
Latest10NTI (Latest.png). Se buscan los píxeles brillantes aislados (la anomalía que MIROVA marca en blanco) y
se ubican en km desde el centro de la miniatura, SUPONIENDO que la miniatura es la grilla de MIROVA de 51 x 51 km
centrada en mirova_center, norte arriba (supuesto declarado, no leído de la lámina). Control del supuesto: el
cráter debe caer a ~4,9 km rumbo ~330° del centro. Se compara con la posición de nuestro píxel alertado más
potente de la misma pasada (record K), en km y rumbo desde el mismo centro.

Uso: python -I v6_miniaturas_direccion.py <dir_imagenes>
"""
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
D = Path(sys.argv[1])
MC = (-33.42694, -69.80039)
VENT = (-33.389044, -69.826374)
LADO_KM = 51.0
# (archivo, celda: índice de columna 0-4 en la fila de arriba, pasada, sensor)
CASOS = [("2026-09-28_05-18-00", 1, "2026-09-28 05:18", "VIIRS_SNPP"),
         ("2026-09-28_05-18-00", 0, "2026-09-28 05:36", "VIIRS_NOAA20"),
         ("2026-09-29_04-54-00", 3, "2026-09-29 04:54", "VIIRS_SNPP"),
         ("2026-09-29_04-54-00", 2, "2026-09-29 05:18", "VIIRS_NOAA20"),
         ("2026-09-14_06-18-00", 1, "2026-09-14 06:18", "VIIRS_SNPP"),
         ("2026-08-01_05-00-00", 2, "2026-08-01 05:00", "VIIRS_SNPP")]


def km_rumbo(a, b):
    """(dx_este, dy_norte) en km de a -> b, aproximación plana."""
    dy = (b[0] - a[0]) * 111.32
    dx = (b[1] - a[1]) * 111.32 * math.cos(math.radians(0.5 * (a[0] + b[0])))
    return dx, dy


def fmt(dx, dy):
    return f"{math.hypot(dx, dy):5.1f} km rumbo {(math.degrees(math.atan2(dx, dy)) + 360) % 360:5.0f}°"


recs = {(r["sensor"], r["datetime_utc"]): r
        for r in json.load(open(ROOT / "data" / "mirova_equivalent" / "Tupungatito.json", encoding="utf-8"))["records"]}
out = []
P = out.append
dxv, dyv = km_rumbo(MC, VENT)
P(f"supuesto: miniatura = {LADO_KM} km de lado centrada en mirova_center {MC}, norte arriba")
P(f"cráter (vent) desde el centro: {fmt(dxv, dyv)}")
for arch, col, pasada, sensor in CASOS:
    im = np.array(Image.open(D / f"{arch}_Tupungatito_VIIRS375_Latest.png").convert("RGB")).astype(int)
    x0c = 8 + col * 166          # las celdas de la fila de arriba empiezan en x ~ 12 + 166 k
    sub = im[160:320, x0c:x0c + 162]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    # todo lo que no es el fondo gris (242) del panel: la miniatura con su marco
    marco = (np.abs(r - 242) > 3) | (np.abs(g - 242) > 3) | (np.abs(b - 242) > 3)
    filas = np.where(marco.mean(1) > 0.6)[0]
    cols = np.where(marco.mean(0) > 0.6)[0]
    if len(filas) < 2 or len(cols) < 2:
        P(f"\n{pasada}: marco no encontrado"); continue
    y0, y1, x0, x1 = filas.min(), filas.max(), cols.min(), cols.max()
    inner = sub[y0 + 3:y1 - 2, x0 + 3:x1 - 2].mean(2)
    h, w = inner.shape
    # brillante aislado: muy por encima de la mediana de su entorno 7x7
    med = ndimage.median_filter(inner, size=7)
    cand = (inner > 200) & (inner - med > 45)
    cand[:4, :] = cand[-4:, :] = False      # los bordes de la miniatura dan falsos puntos
    cand[:, :4] = cand[:, -4:] = False
    lab, n = ndimage.label(cand)
    P(f"\n{pasada} {sensor} (lámina {arch}, celda {col}): marco x {x0}-{x1}, y {y0}-{y1}; interior {w} x {h} px; "
      f"{n} punto(s) brillante(s) aislado(s)")
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        yc = (sl[0].start + sl[0].stop - 1) / 2.0
        xc = (sl[1].start + sl[1].stop - 1) / 2.0
        dx = (xc - (w - 1) / 2.0) * LADO_KM / w
        dy = -(yc - (h - 1) / 2.0) * LADO_KM / h
        P(f"   MIROVA punto en ({xc:.0f}, {yc:.0f}) px, brillo {inner[sl].max():.0f} sobre mediana local "
          f"{med[sl].min():.0f} -> {fmt(dx, dy)} desde el centro")
    rec = recs.get((sensor, pasada))
    if rec:
        pix = sorted(rec.get("anomaly_pixels") or [], key=lambda p: -p["vrp_mw"])[:3]
        for p in pix:
            dx, dy = km_rumbo(MC, (p["lat"], p["lon"]))
            P(f"   nuestro píxel {p['vrp_mw']:.3f} MW, {p['bt_k']} K -> {fmt(dx, dy)} desde el centro")
txt = "\n".join(out)
print(txt)
(AQUI / "v6_miniaturas_direccion_salida.txt").write_text(txt + "\n", encoding="utf-8")
