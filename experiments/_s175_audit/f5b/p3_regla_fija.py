# -*- coding: utf-8 -*-
"""P3 (F5b): derivar una REGLA FIJA de recorte (dónde empieza y cuánto mide la imagen dentro del marco del panel) y
validarla en los 4 casos con TIF, dejando fuera el caso que se valida (uno afuera por vez).

Por qué: después del 22-sep no hay TIF con que afinar el mapeo caso a caso (p1 lo afinaba por correlación con el
TIF de la misma pasada). Hace falta una regla que dependa sólo del marco del panel. p2 mostró que el dibujo está
interpolado (0 columnas duplicadas en VIIRS 375), así que la fase se mide por correlación subpíxel contra el TIF
en los casos con TIF, se expresa como margen respecto del bbox exterior del marco, y se comprueba que el margen sea
el mismo en los 4 casos (si no lo es, no hay regla fija y el PNG no sirve de vara).

Modelo: imagen = [bx0 + mL, bx1 + 1 - mR] en x y [by0 + mT, by1 + 1 - mB] en y, con (bx0, by0, bx1, by1) el bbox
exterior del marco (píxeles enteros, inclusivos). Se barre mL, mR, mT, mB de 0 a 5 px en pasos de 0,25 px
maximizando la correlación entre el panel (luminancia) y el TIF (log10) remuestreado bilinealmente.

Pregunta 1: si el panel no fuera la grilla, la correlación máxima sería baja (se imprime) y los márgenes no coincidirían
entre casos. Pregunta 2: si el remuestreo estuviera muerto, la correlación sería NaN o la misma para todo margen.
Control positivo (uno afuera): con los márgenes medianos de los OTROS tres casos, el píxel más claro del panel cae a
menos de la tolerancia de F5 del máximo del TIF dentro del inner.

Uso: python -I p3_regla_fija.py. Salida: p3_regla_fija_out.json y stdout.
"""
import itertools, json, math, os, sys
import numpy as np
import rasterio
from rasterio.warp import transform as rtransform
from scipy.ndimage import map_coordinates
from PIL import Image
import yaml

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
TIFS = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\tif_descargas"
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
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


def bbox_marco(im, k=0):
    """bbox exterior (x0, y0, x1, y1 inclusivos) del marco del panel k; marco verde (alerta) o gris."""
    col, row = k % 5, k // 5
    x0, y0 = 5 + 165 * col, 155 + 236 * row
    sub = im[y0:y0 + 175, x0:x0 + 165].astype(int)
    bg = (np.abs(sub - 242).max(axis=2) <= 3)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    frame = ((g > 200) & (r < 140) & (b < 140)) | ((np.abs(r - g) < 4) & (np.abs(g - b) < 4) & (r > 60) & (r < 200) & ~bg)
    ys, xs = np.where(frame)
    return x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max()


def remuestrear(la, X0, Y0, W, Hh, px_x, px_y):
    """Valor bilineal del TIF (n x n) en los centros de los píxeles absolutos px_x (columnas) y px_y (filas)."""
    n = la.shape[0]
    cx = (px_x + 0.5 - X0) / W * n - 0.5
    cy = (px_y + 0.5 - Y0) / Hh * n - 0.5
    gy, gx = np.meshgrid(cy, cx, indexing="ij")
    return map_coordinates(la, [gy.ravel(), gx.ravel()], order=1, mode="constant", cval=np.nan).reshape(gy.shape)


def corr(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 50:
        return float("nan")
    return float(np.corrcoef(x[ok], y[ok])[0, 1])


def main():
    datos = []
    for vol, b, dt, tif, png in CASOS:
        im = np.array(Image.open(os.path.join(TMP, "png", png)).convert("RGB"))
        bx0, by0, bx1, by1 = bbox_marco(im, 0)
        with rasterio.open(os.path.join(TIFS, tif)) as ds:
            a = ds.read(1).astype(float)
            if ds.nodata is not None:
                a[a == ds.nodata] = np.nan
            tr, crs = ds.transform, ds.crs
        n = a.shape[0]
        la = np.log10(np.clip(a, 1e-6, None))
        la_f = np.where(np.isfinite(la), la, np.nanmedian(la))
        # píxeles del panel claramente interiores (5 px adentro del bbox exterior) para la correlación
        px_x = np.arange(bx0 + 5, bx1 - 4)
        px_y = np.arange(by0 + 5, by1 - 4)
        L = im[by0 + 5:by1 - 4, bx0 + 5:bx1 - 4].astype(float).mean(axis=2)
        # barrido: x e y por separado (la correlación 2-D se maximiza por descenso en coordenadas, 2 vueltas)
        pasos = np.arange(0.0, 5.001, 0.25)
        mL, mR, mT, mB = 2.0, 2.0, 2.0, 2.0
        for _ in range(2):
            best = (-2, None)
            for a_, b_ in itertools.product(pasos, pasos):
                X0, W = bx0 + a_, (bx1 + 1 - b_) - (bx0 + a_)
                Y0, Hh = by0 + mT, (by1 + 1 - mB) - (by0 + mT)
                c = corr(remuestrear(la_f, X0, Y0, W, Hh, px_x, px_y), L)
                if c > best[0]:
                    best = (c, (a_, b_))
            mL, mR = best[1]
            best = (-2, None)
            for a_, b_ in itertools.product(pasos, pasos):
                X0, W = bx0 + mL, (bx1 + 1 - mR) - (bx0 + mL)
                Y0, Hh = by0 + a_, (by1 + 1 - b_) - (by0 + a_)
                c = corr(remuestrear(la_f, X0, Y0, W, Hh, px_x, px_y), L)
                if c > best[0]:
                    best = (c, (a_, b_))
            mT, mB = best[1]
        cmax = best[0]
        datos.append(dict(vol=vol, b=b, dt=dt, tif=tif, png=png, bbox=[int(bx0), int(by0), int(bx1), int(by1)], n=n,
                          margenes_LRTB=[float(mL), float(mR), float(mT), float(mB)], corr_max=round(cmax, 4),
                          _a=a, _tr=tr, _crs=crs, _im=im))
        print(json.dumps({k: v for k, v in datos[-1].items() if not k.startswith("_")}, ensure_ascii=False))

    # Regla fija por sensor y validación uno afuera
    out = []
    for i, d in enumerate(datos):
        otros = [e for j, e in enumerate(datos) if j != i]
        # mediana de los márgenes de los otros tres (sin distinguir sensor: el marco es el mismo dibujo)
        m = np.median([e["margenes_LRTB"] for e in otros], axis=0)
        mL, mR, mT, mB = m
        bx0, by0, bx1, by1 = d["bbox"]
        X0, W = bx0 + mL, (bx1 + 1 - mR) - (bx0 + mL)
        Y0, Hh = by0 + mT, (by1 + 1 - mB) - (by0 + mT)
        a, tr, crs, im, n = d["_a"], d["_tr"], d["_crs"], d["_im"], d["n"]
        rr, cc = np.meshgrid(range(n), range(n), indexing="ij")
        xs, ys = rasterio.transform.xy(tr, rr.ravel(), cc.ravel())
        lons, lats = rtransform(crs, "EPSG:4326", list(xs), list(ys))
        lats, lons = np.array(lats).reshape(a.shape), np.array(lons).reshape(a.shape)
        mc = (V[d["vol"]]["mirova_center_lat"], V[d["vol"]]["mirova_center_lon"])
        inner = np.vectorize(lambda la_, lo_: hav(la_, lo_, *mc))(lats, lons) <= V[d["vol"]]["inner_radius_km"]
        # panel entero (píxeles del interior del marco) y máscaras llevadas al panel por vecino más cercano
        px_x = np.arange(math.ceil(X0), math.floor(X0 + W))
        px_y = np.arange(math.ceil(Y0), math.floor(Y0 + Hh))
        L = im[px_y[0]:px_y[-1] + 1, px_x[0]:px_x[-1] + 1].astype(float).mean(axis=2)
        cx = np.clip(((px_x + 0.5 - X0) / W * n).astype(int), 0, n - 1)
        cy = np.clip(((px_y + 0.5 - Y0) / Hh * n).astype(int), 0, n - 1)
        inner_p = inner[np.ix_(cy, cx)]
        nan_p = np.isnan(a)[np.ix_(cy, cx)]
        Lm = np.where(inner_p & ~nan_p, L, -1)
        top = np.argwhere(Lm >= Lm.max() - 0.5)
        pyc, pxc = top.mean(axis=0)
        ri = int(np.clip((px_y[0] + pyc + 0.5 - Y0) / Hh * n, 0, n - 1))
        ci = int(np.clip((px_x[0] + pxc + 0.5 - X0) / W * n, 0, n - 1))
        am = np.where(inner, a, np.nan)
        iy, ix = np.unravel_index(np.nanargmax(am), am.shape)
        dkm = hav(lats[ri, ci], lons[ri, ci], lats[iy, ix], lons[iy, ix])
        o = {k: v for k, v in d.items() if not k.startswith("_")}
        o.update({"regla_otros_tres_LRTB": [round(float(x), 3) for x in m], "X0_Y0_W_H": [round(X0, 2), round(Y0, 2), round(W, 2), round(Hh, 2)],
                  "px_por_celda": round(W / n, 4), "png_max_rc": [ri, ci], "png_max_latlon": [round(float(lats[ri, ci]), 5), round(float(lons[ri, ci]), 5)],
                  "tif_max_rc": [int(iy), int(ix)], "tif_max_latlon": [round(float(lats[iy, ix]), 5), round(float(lons[iy, ix]), 5)],
                  "d_png_tif_km": round(dkm, 3), "d_pix": round(math.hypot(ri - iy, ci - ix), 2), "tol_km": TOL[d["b"]], "valida": bool(dkm <= TOL[d["b"]])})
        out.append(o)
        print(json.dumps(o, ensure_ascii=False))
    mg = np.median([d["margenes_LRTB"] for d in datos], axis=0)
    print("REGLA FIJA (mediana de los 4, L R T B):", [round(float(x), 3) for x in mg], " dispersión (max-min):",
          [round(float(x), 2) for x in (np.max([d["margenes_LRTB"] for d in datos], axis=0) - np.min([d["margenes_LRTB"] for d in datos], axis=0))])
    print("VALIDA uno afuera:", sum(o["valida"] for o in out), "de", len(out))
    json.dump({"casos": out, "regla_fija_LRTB": [float(x) for x in mg]}, open(os.path.join(H, "p3_regla_fija_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
