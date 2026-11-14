# -*- coding: utf-8 -*-
"""Biblioteca de F5b: geometría del panel de la lámina Latest10NTI de MIROVA, regla fija de recorte (p3), grilla
prestada de un TIF, píxel más claro dentro del inner y lectura OCR de las etiquetas.

Regla fija (p3_regla_fija.out.txt, mediana de 4 casos con TIF, correlación 0,992 a 0,994): la imagen ocupa
[bx0 + 3, bx1 + 1 - 0] en x y [by0 + 1,5, by1 + 1 - 1,5] en y, con (bx0, by0, bx1, by1) el bbox exterior del marco.
Precisión validada: 1 celda (0,37 km VIIRS 375, 0,75 km VIIRS 750) en 4 de 4 con uno afuera.
"""
import math, os, re
import numpy as np
import rasterio
from rasterio.warp import transform as rtransform
from scipy import ndimage
from PIL import Image

REGLA_LRTB = (3.0, 0.0, 1.5, 1.5)
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
N_CELDAS = {"VIIRS375": 134, "VIIRS750": 67, "MODIS": 51}


def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


def abrir_png(fn):
    return np.array(Image.open(fn).convert("RGB"))


def bbox_marco(im, k=0):
    """Marco del panel k (0 a 9; 5 columnas x 2 filas): centros de las cuatro líneas del marco (cxL, cyT, cxR, cyB) en
    píxeles absolutos, más si es verde (alerta). El marco verde tiene 3 px y el gris de «sin alerta» 1 px, así que el
    bbox exterior no es comparable entre los dos; el centro de la línea sí (peso = qué tan de marco es cada píxel:
    verde puro o gris 204 = 1, antialias = 0,5). Devuelve None si no hay marco (panel vacío)."""
    col, row = k % 5, k // 5
    # la celda empieza en y = 161 (bajo la etiqueta de fecha, que es roja y saturada); el marco superior está en ~163
    x0, y0 = 5 + 165 * col, 161 + 236 * row
    # la celda termina en y0 + 158 (~319): bajo el marco inferior (~315) y sobre el texto rojo «VRP = x MW» (~321)
    sub = im[y0:y0 + 158, x0:x0 + 165].astype(float)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    mx, mn = sub.max(axis=2), sub.min(axis=2)
    # marco de color: verde (VERY LOW, LOW), amarillo (MODERATE, visto en Chillán 2026-10-18), probablemente rojo (HIGH);
    # peso = saturación (max - min) / 255 en píxeles claros. El interior gris azulado tiene saturación ~0,1.
    w_color = np.clip((mx - mn) / 255.0, 0, 1) * (mx >= 200)
    gris = (np.abs(r - g) < 3) & (np.abs(g - b) < 3) & (r >= 195) & (r <= 235)
    w_gris = np.clip((242.0 - r) / (242.0 - 204.0), 0, 1) * gris
    # es marco de color si alguna columna entera es de color (una línea de ~150 px); la suma total engaña (interior claro)
    verde = bool(w_color.sum(axis=0).max() >= 60)
    w = w_color if verde else w_gris
    colsum, rowsum = w.sum(axis=0), w.sum(axis=1)
    cols = np.where(colsum >= 60)[0]
    rows = np.where(rowsum >= 60)[0]
    if len(cols) < 2 or len(rows) < 2:
        return None
    # líneas: izquierda = columnas de marco en el tercio izquierdo, derecha = en el tercio derecho (ídem filas)
    mid_c, mid_r = (cols.min() + cols.max()) / 2.0, (rows.min() + rows.max()) / 2.0
    cL, cR = cols[cols < mid_c], cols[cols > mid_c]
    rT, rB = rows[rows < mid_r], rows[rows > mid_r]
    cxL = float((colsum[cL] * cL).sum() / colsum[cL].sum())
    cxR = float((colsum[cR] * cR).sum() / colsum[cR].sum())
    cyT = float((rowsum[rT] * rT).sum() / rowsum[rT].sum())
    cyB = float((rowsum[rB] * rB).sum() / rowsum[rB].sum())
    return round(x0 + cxL, 2), round(y0 + cyT, 2), round(x0 + cxR, 2), round(y0 + cyB, 2), bool(verde)


# Regla fija expresada contra el centro de las líneas del marco (equivalente a REGLA_LRTB sobre el bbox exterior del
# marco verde de p3: bbox 12..165 -> X0 15, X1 166; centros 13,4 y 164,7): la imagen va de cxL + DX a cxR + DX en x y de
# cyT a cyB en y.
DX_IMAGEN = 1.5


def geometria(bbox, dx=DX_IMAGEN):
    cxL, cyT, cxR, cyB = bbox[:4]
    return cxL + dx, cyT, cxR - cxL, cyB - cyT


def grilla(tif):
    """lat y lon (n x n) de los centros de celda del TIF, más el arreglo y la transformación."""
    with rasterio.open(tif) as ds:
        a = ds.read(1).astype(float)
        if ds.nodata is not None:
            a[a == ds.nodata] = np.nan
        n = ds.height
        rr, cc = np.meshgrid(range(n), range(ds.width), indexing="ij")
        xs, ys = rasterio.transform.xy(ds.transform, rr.ravel(), cc.ravel())
        lons, lats = rtransform(ds.crs, "EPSG:4326", list(xs), list(ys))
        return {"a": a, "lats": np.array(lats).reshape(a.shape), "lons": np.array(lons).reshape(a.shape), "n": n,
                "transform": ds.transform, "crs": str(ds.crs)}


def mascara_inner(g, mc, inner_km):
    return np.vectorize(lambda la_, lo_: hav(la_, lo_, *mc))(g["lats"], g["lons"]) <= inner_km


def recorte(im, X0, Y0, W, Hh):
    px_x = np.arange(math.ceil(X0), math.floor(X0 + W))
    px_y = np.arange(math.ceil(Y0), math.floor(Y0 + Hh))
    pan = im[px_y[0]:px_y[-1] + 1, px_x[0]:px_x[-1] + 1]
    return pan, px_x, px_y


def celdas_de(px_x, px_y, X0, Y0, W, Hh, n):
    cx = np.clip(((px_x + 0.5 - X0) / W * n).astype(int), 0, n - 1)
    cy = np.clip(((px_y + 0.5 - Y0) / Hh * n).astype(int), 0, n - 1)
    return cy, cx


def pixel_mas_claro(im, bbox, g, inner, nan_tif=None, min_area_nan=20):
    """Píxel más claro del panel dentro del inner, fuera del blanco de «sin dato».
    Sin TIF de la pasada, el «sin dato» se reconoce como componente blanca (min RGB > 245) de area >= min_area_nan px,
    dilatada 1 px. Devuelve dict con fila/col de celda, lat/lon, tamaño de la mancha, luminancias y máscaras usadas."""
    X0, Y0, W, Hh = geometria(bbox)
    pan, px_x, px_y = recorte(im, X0, Y0, W, Hh)
    L = pan.astype(float).mean(axis=2)
    n = g["n"]
    cy, cx = celdas_de(px_x, px_y, X0, Y0, W, Hh, n)
    inner_p = inner[np.ix_(cy, cx)]
    blanco = pan.min(axis=2) > 245
    lab, nlab = ndimage.label(blanco)
    sizes = ndimage.sum(blanco, lab, range(1, nlab + 1))
    grande = np.isin(lab, [i + 1 for i, s_ in enumerate(sizes) if s_ >= min_area_nan])
    nanmask = ndimage.binary_dilation(grande, iterations=1)
    if nan_tif is not None:
        nanmask |= nan_tif[np.ix_(cy, cx)]
    Lm = np.where(inner_p & ~nanmask, L, -1.0)
    if Lm.max() < 0:
        return None
    py, px = np.unravel_index(np.argmax(Lm), Lm.shape)
    # mancha: componente conexa (8 vecinos) de píxeles a menos de 10 niveles del máximo que contiene al máximo
    cand = Lm >= Lm.max() - 10
    lab2, _ = ndimage.label(cand, structure=np.ones((3, 3)))
    mancha = lab2 == lab2[py, px]
    pyc, pxc = ndimage.center_of_mass(mancha)
    ri = int(np.clip((px_y[0] + pyc + 0.5 - Y0) / Hh * n, 0, n - 1))
    ci = int(np.clip((px_x[0] + pxc + 0.5 - X0) / W * n, 0, n - 1))
    return {"rc": [ri, ci], "lat": float(g["lats"][ri, ci]), "lon": float(g["lons"][ri, ci]), "lum_max": float(Lm.max()),
            "lum_p99_panel": float(np.percentile(L, 99)), "lum_mediana_panel": float(np.median(L)), "mancha_px": int(mancha.sum()),
            "blancos_sin_dato_px": int(grande.sum()), "px_por_celda": W / n, "panel_px": [int(pan.shape[1]), int(pan.shape[0])]}


# ---- OCR ----------------------------------------------------------------------------------------------------------
_RE = re.compile(r"(\d{2})-([A-Za-z]{3})-(\d{4})\s*(\d{2}):(\d{2}):(\d{2})")
_MES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def _tess():
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    return pytesseract


def leer_fecha(img, escala=3):
    """Texto de una franja y su fecha 'YYYY-MM-DD HH:MM:SS' si se reconoce (None si no)."""
    pt = _tess()
    g = img.convert("L").resize((img.width * escala, img.height * escala), Image.LANCZOS)
    a = np.where(np.array(g) < 170, 0, 255).astype(np.uint8)
    t = None
    for intento in range(3):   # p8 v0: tesseract murió con 3221225773 (STATUS_INVALID_PARAMETER) corriendo en segundo plano
        try:
            t = pt.image_to_string(Image.fromarray(a), config="--psm 7 -c tessedit_char_whitelist=0123456789-:JanFebMrApyulgSOctNovDLstUpdae ")
            break
        except pt.TesseractError as e:
            err = e
    if t is None:
        return "OCR_ERROR %r" % (err,), None
    m = _RE.search(t)
    if not m or m.group(2) not in _MES:
        return t.strip(), None
    d, mo, y, hh, mm, ss = m.groups()
    return t.strip(), "%s-%02d-%s %s:%s:%s" % (y, _MES[mo], d, hh, mm, ss)


def etiquetas(fn):
    """Cabecera «Last Update» y las 10 etiquetas de panel de una lámina."""
    im = Image.open(fn).convert("RGB")
    cab = leer_fecha(im.crop((85, 45, 440, 78)))
    pan = []
    for k in range(10):
        col, row = k % 5, k // 5
        x0, y0 = 8 + 165 * col, 146 + 236 * row
        pan.append(leer_fecha(im.crop((x0, y0, x0 + 162, y0 + 16))))
    return cab, pan
