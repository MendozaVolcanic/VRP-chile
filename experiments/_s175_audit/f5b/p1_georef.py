# -*- coding: utf-8 -*-
"""P1 (F5b): georreferenciar el panel 1 de la lámina Latest10NTI de MIROVA contra el TIF de la misma pasada.

Por qué: desde el 2026-09-22 el archivo no captura TIF, sólo láminas PNG. Si el panel 1 de la lámina es la grilla
completa del TIF dibujada sin ejes (imagesc), un píxel del panel se convierte en fila y columna del TIF por una
escala fija y de ahí a lat/lon con la transformación del TIF. Esto se valida acá, con las 4 pasadas de F5 que
tienen TIF y georreferencia que reproduce la distancia de la tabla.

Las dos preguntas del instrumento:
 1. Si el panel NO fuera la grilla del TIF (recorte, otra orientación, otro producto), la correlación entre el panel
    y el TIF remuestreado sería baja y las orientaciones alternativas (volteos, rotaciones) no quedarían por debajo:
    se imprimen las 8 orientaciones y la correlación de cada una (control negativo por construcción).
 2. Si el instrumento estuviera muerto (panel mal recortado, TIF vacío), la correlación sería NaN o cercana a 0 y
    el píxel más claro caería en el NaN blanco del borde de la pasada: se enmascara con el NaN del TIF y se informa
    cuántos píxeles blancos quedan dentro y fuera de la máscara.
Control positivo: el píxel más claro del panel, llevado a lat/lon, tiene que caer a menos de la tolerancia de F5
(2 píxeles nominales VIIRS: 0,75 km en 375 y 1,5 km en 750; 3 km MODIS) del píxel máximo del TIF dentro del inner
(el mismo criterio de experiments/_s175_audit/f5/i2_tif.py).

Uso: python -I p1_georef.py   (rutas fijas abajo). Salida: p1_georef_out.json y stdout.
"""
import json, math, os, sys
import numpy as np
import rasterio
from rasterio.warp import transform as rtransform
from PIL import Image
import yaml

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
TIFS = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\tif_descargas"   # bajados por F5, md5 cotejados con el índice (p0)
VOLC = yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]
V = {v["name"]: v for v in VOLC}
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
CASOS = [
    ("Lastarria", "VIIRS375", "2026-06-12 05:54", "20260612_055401_VIIRS375.tif", "20260612_153203_VIIRS375_Latest10NTI.png"),
    ("Lastarria", "VIIRS375", "2026-08-09 05:48", "20260809_054800_VIIRS375.tif", "20260809_082023_VIIRS375_Latest10NTI.png"),
    ("Lascar", "VIIRS750", "2026-06-21 05:30", "20260621_053002_VIIRS750.tif", "20260621_092513_VIIRS750_Latest10NTI.png"),
    ("Isluga", "VIIRS375", "2026-09-22 05:42", "20260922_054201_VIIRS375.tif", "20260922_092431_VIIRS375_Latest10NTI.png"),
]


def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


def panel_interior(im, k=0):
    """Interior (x0, y0, x1, y1 inclusivos) del panel k (0 a 9) de la lámina de 850 x 600.
    El marco es verde (alerta) o gris; se busca el rectángulo de píxeles que no son fondo (242) en la celda del panel."""
    col, row = k % 5, k // 5
    # celdas aproximadas: los paneles empiezan en x = 13 + 165 * col, y = 164 + 236 * row (medido en la lámina de Isluga)
    x0, y0 = 5 + 165 * col, 155 + 236 * row
    sub = im[y0:y0 + 175, x0:x0 + 165].astype(int)
    bg = (np.abs(sub - 242).max(axis=2) <= 3)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    frame = ((g > 200) & (r < 140) & (b < 140)) | ((np.abs(r - g) < 4) & (np.abs(g - b) < 4) & (r > 60) & (r < 200) & ~bg)
    ys, xs = np.where(frame)
    # el marco es el borde exterior: su bbox
    fx0, fx1, fy0, fy1 = xs.min(), xs.max(), ys.min(), ys.max()
    # grosor: contar píxeles de marco consecutivos desde el borde izquierdo en la fila central
    midy = (fy0 + fy1) // 2
    t = 0
    while frame[midy, fx0 + t]:
        t += 1
    # La imagen de matplotlib llega hasta el CENTRO de la línea del marco (la línea se dibuja encima del borde de la
    # imagen). Primera corrida (p1_georef_v0.out.txt): recortando el marco entero quedaba un sesgo de 1 celda y la
    # búsqueda fina pedía escala 1,02 a 1,03 y (dx, dy) = (-1, -2). Extensión usada: de centro a centro del marco.
    half = t / 2.0
    return x0 + fx0 + half, y0 + fy0 + half, x0 + fx1 - half, y0 + fy1 - half, t


def lum(im):
    return im[..., :3].astype(float).mean(axis=2)


def resample(a, w, h, X0=0.0, Y0=0.0, W=None, Hh=None, s=1.0, dx=0, dy=0):
    """TIF (n x m) remuestreado por vecino más cercano a los píxeles del recorte entero del panel (h filas, w columnas).
    El recorte entero empieza en (cx0, cy0) = ceil de la extensión fraccionaria; el centro del píxel k del recorte está en
    cx0 + k + 0,5 y la celda es ((cx0 + k + 0,5 - X0 - dx) / (W * s)) * m. Con X0 = 0 y W = w es el mapeo simple."""
    n, m = a.shape
    W = w if W is None else W
    Hh = h if Hh is None else Hh
    cx0, cy0 = math.ceil(X0), math.ceil(Y0)
    rows = (((cy0 + np.arange(h) + 0.5 - Y0 - dy) / (Hh * s)) * n).astype(int)
    cols = (((cx0 + np.arange(w) + 0.5 - X0 - dx) / (W * s)) * m).astype(int)
    okr = (rows >= 0) & (rows < n)
    okc = (cols >= 0) & (cols < m)
    R = np.full((h, w), np.nan)
    R[np.ix_(okr, okc)] = a[np.ix_(rows[okr], cols[okc])]
    return R


def panel_a_celda(py, px, n, X0, Y0, W, Hh, s=1.0, dx=0, dy=0):
    """Fila y columna del TIF (n x n) del píxel (py, px) del recorte entero del panel."""
    cx0, cy0 = math.ceil(X0), math.ceil(Y0)
    r = int(((cy0 + py + 0.5 - Y0 - dy) / (Hh * s)) * n)
    c = int(((cx0 + px + 0.5 - X0 - dx) / (W * s)) * n)
    return min(max(r, 0), n - 1), min(max(c, 0), n - 1)


def corr(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 50:
        return float("nan")
    x, y = x[ok], y[ok]
    return float(np.corrcoef(x, y)[0, 1])


ORIENT = {"id": lambda a: a, "fliplr": np.fliplr, "flipud": np.flipud, "rot90": lambda a: np.rot90(a, 1),
          "rot180": lambda a: np.rot90(a, 2), "rot270": lambda a: np.rot90(a, 3), "T": lambda a: a.T,
          "antiT": lambda a: np.rot90(a, 2).T}


def main():
    out = []
    for vol, b, dt, tif, png in CASOS:
        im = np.array(Image.open(os.path.join(TMP, "png", png)).convert("RGB"))
        X0, Y0, X1, Y1, t = panel_interior(im, 0)
        W, Hh = X1 - X0, Y1 - Y0                       # extensión fraccionaria de la imagen (centro a centro del marco)
        cx0, cy0, cx1, cy1 = math.ceil(X0), math.ceil(Y0), math.floor(X1), math.floor(Y1)
        pan = im[cy0:cy1 + 1, cx0:cx1 + 1]             # recorte entero
        L = lum(pan)
        h, w = L.shape
        M = dict(X0=X0, Y0=Y0, W=W, Hh=Hh)
        with rasterio.open(os.path.join(TIFS, tif)) as ds:
            a = ds.read(1).astype(float)
            if ds.nodata is not None:
                a[a == ds.nodata] = np.nan
            tr, crs = ds.transform, ds.crs
        n = a.shape[0]
        # 1. correlación en las 8 orientaciones (el TIF en log para aplanar el píxel caliente)
        la = np.log10(np.clip(a, 1e-6, None))
        cors = {}
        for name, f in ORIENT.items():
            R = resample(f(la), w, h, **M)
            cors[name] = round(corr(R, L), 3)
        # 2. búsqueda fina alrededor del mapeo nominal (escala y desplazamiento) con la orientación identidad
        best = (-2, None)
        for s_ in np.arange(0.96, 1.041, 0.01):
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    c = corr(resample(la, w, h, s=s_, dx=dx, dy=dy, **M), L)
                    if c > best[0]:
                        best = (c, (round(float(s_), 2), dx, dy))
        s_b, dx_b, dy_b = best[1]
        # 3. píxel más claro del panel dentro del inner y fuera del NaN del TIF
        Rnan = resample(np.isnan(a).astype(float), w, h, **M) > 0.5
        rr, cc = np.meshgrid(range(n), range(n), indexing="ij")
        xs, ys = rasterio.transform.xy(tr, rr.ravel(), cc.ravel())
        lons, lats = rtransform(crs, "EPSG:4326", list(xs), list(ys))
        lats = np.array(lats).reshape(a.shape)
        lons = np.array(lons).reshape(a.shape)
        mc = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        dd = np.vectorize(lambda la_, lo_: hav(la_, lo_, *mc))(lats, lons)
        inner = dd <= V[vol]["inner_radius_km"]
        Rinner = resample(inner.astype(float), w, h, **M) > 0.5
        white_total = int((pan.min(axis=2) > 245).sum())
        white_in_nan = int(((pan.min(axis=2) > 245) & Rnan).sum())
        Lm = np.where(Rinner & ~Rnan, L, -1)
        py, px = np.unravel_index(np.argmax(Lm), Lm.shape)
        # todos los píxeles del panel con la luminancia máxima (un píxel de grilla ocupa ~1,1 px)
        top = np.argwhere(Lm >= Lm.max() - 0.5)
        pyc, pxc = top.mean(axis=0)
        ri, ci = panel_a_celda(pyc, pxc, n, **M)                              # mapeo nominal
        rf, cf = panel_a_celda(pyc, pxc, n, s=s_b, dx=dx_b, dy=dy_b, **M)     # mapeo afinado por correlación
        lat_png, lon_png = float(lats[ri, ci]), float(lons[ri, ci])
        lat_f, lon_f = float(lats[rf, cf]), float(lons[rf, cf])
        # vara: máximo del TIF dentro del inner (criterio de i2_tif.py)
        am = np.where(inner, a, np.nan)
        iy, ix = np.unravel_index(np.nanargmax(am), am.shape)
        lat_tif, lon_tif = float(lats[iy, ix]), float(lons[iy, ix])
        d_km = hav(lat_png, lon_png, lat_tif, lon_tif)
        d_pix = math.hypot(ri - iy, ci - ix)
        # control: ¿el píxel del panel que corresponde al máximo del TIF es también claro?
        pyt = min(max(int(round((iy + 0.5) / n * Hh + Y0 - 0.5)) - cy0, 0), h - 1)
        pxt = min(max(int(round((ix + 0.5) / n * W + X0 - 0.5)) - cx0, 0), w - 1)
        d_fino = hav(lat_f, lon_f, lat_tif, lon_tif)
        o = {"vol": vol, "b": b, "dt": dt, "tif": tif, "png": png, "extension_xyxy": [round(X0, 1), round(Y0, 1), round(X1, 1), round(Y1, 1)],
             "marco_px": int(t), "panel_wh": [int(w), int(h)], "tif_n": int(n), "px_por_celda": round(W / n, 3),
             "png_max_afinado_rc": [rf, cf], "png_max_afinado_latlon": [round(lat_f, 5), round(lon_f, 5)], "d_afinado_tif_km": round(d_fino, 3),
             "corr_orientaciones": cors, "mejor_fino": {"corr": round(best[0], 3), "escala_dx_dy": best[1]},
             "blancos_panel": white_total, "blancos_en_nan_tif": white_in_nan, "n_px_max_panel": int(len(top)),
             "png_max_rc": [ri, ci], "png_max_latlon": [round(lat_png, 5), round(lon_png, 5)], "lum_max": round(float(Lm.max()), 1),
             "tif_max_rc": [int(iy), int(ix)], "tif_max_latlon": [round(lat_tif, 5), round(lon_tif, 5)],
             "lum_panel_en_tif_max": round(float(L[pyt, pxt]), 1), "lum_p99_panel": round(float(np.percentile(L, 99)), 1),
             "d_png_tif_km": round(d_km, 3), "d_png_tif_pix": round(d_pix, 2), "tol_km": TOL[b], "valida": bool(d_km <= TOL[b])}
        out.append(o)
        print(json.dumps(o, ensure_ascii=False))
    json.dump(out, open(os.path.join(H, "p1_georef_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("VALIDA", sum(o["valida"] for o in out), "de", len(out))


if __name__ == "__main__":
    main()
