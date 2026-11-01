# -*- coding: utf-8 -*-
"""S159 frente GEO, parte G (para la ola 2, NO despachado): ajustar el desfase subcelda y el interpolador con que
MIROVA remuestrea un granulo VIIRS a su grilla UTM, comparando contra el TIF de MIROVA de la MISMA adquisicion.

POR QUE: la prueba con granulos de S158 R2 uso la grilla de MIROVA como hipotesis, y dos alertas debiles (Lascar
2026-09-26 05:48, Chaiten 2026-10-06 05:30, VIIRS 750) aparecen o desaparecen al mover la grilla media celda o al
cambiar de interpolador. Este script busca, en vez de suponer, el par (desfase, interpolador) que mejor reproduce
el TIF.

QUE HACE: proyecta las muestras del granulo (centros de pixel, lat/lon de VNP03IMG o equivalente, y la radiancia
de I4 de VNP02IMG) al EPSG del TIF; construye UNA vez cada interpolador sobre esas muestras (vecino mas cercano,
lineal sobre Delaunay, cubico Clough-Tocher); y evalua cada interpolador en los centros de celda del TIF corridos
(dx, dy) en una malla de +/- media celda. Para cada candidato ajusta a + b * modelo por minimos cuadrados (para
absorber diferencias de calibracion NRT/estandar) y mide la raiz del error cuadratico medio relativa a la
desviacion del TIF. Refina alrededor del mejor. Reporta el mejor, el segundo interpolador y la margen.

LIMITES DECLARADOS:
- El cubico de scipy (Clough-Tocher) no es identico al 'cubic' de griddata de MATLAB; 'natural' y 'v4' de MATLAB
  no estan en scipy. Si el mejor es "cubico" con margen chica, se reporta como NO IDENTIFICADO entre suaves.
- El TIF de la misma adquisicion sale del mismo granulo (A109): aqui eso es lo que se quiere (identificar la
  transformacion), no una validacion de deteccion.
- Un TIF EPSG:4326 (fuera de la ventana UTM de A106) no sirve: el script se niega.

Uso (ola 2): python -I g2_ajuste_grilla.py <muestras.npz con lat, lon, val> <tif MIROVA> [--sin-afin]
Prueba con controles sinteticos: g2_prueba_ajuste.py
"""
import io
import sys

import numpy as np
from scipy.interpolate import CloughTocher2DInterpolator, LinearNDInterpolator, NearestNDInterpolator
from scipy.spatial import Delaunay

INTERP = ("vecino", "lineal", "cubico")


def construir(px, py, pv):
    tri = Delaunay(np.c_[px, py])
    return {"vecino": NearestNDInterpolator(np.c_[px, py], pv),
            "lineal": LinearNDInterpolator(tri, pv),
            "cubico": CloughTocher2DInterpolator(tri, pv)}


def centros(ul_x, ul_y, celda, ancho, alto):
    cx = ul_x + celda * (np.arange(ancho) + 0.5)
    cy = ul_y - celda * (np.arange(alto) + 0.5)
    return np.meshgrid(cx, cy)


def costo(modelo, ref, afin=True):
    ok = np.isfinite(modelo) & np.isfinite(ref)
    if ok.sum() < 50:
        return np.inf, ok.sum()
    m, r = modelo[ok], ref[ok]
    if afin:
        A = np.c_[m, np.ones_like(m)]
        coef, *_ = np.linalg.lstsq(A, r, rcond=None)
        res = r - A @ coef
    else:
        res = r - m
    return float(np.sqrt(np.mean(res ** 2)) / (np.std(r) + 1e-30)), int(ok.sum())


def ajustar(px, py, pv, ref, ul_x, ul_y, celda, mascara=None, afin=True, paso_grueso=None, paso_fino=None):
    """Devuelve lista de dict(interp, dx, dy, costo, n) para la malla gruesa + refinamiento, y el mejor."""
    alto, ancho = ref.shape
    X, Y = centros(ul_x, ul_y, celda, ancho, alto)
    ref = ref.astype(float).copy()
    ref[~np.isfinite(ref) | (ref <= 0)] = np.nan
    if mascara is not None:
        ref[~mascara] = np.nan
    fun = construir(px, py, pv)
    paso_grueso = paso_grueso or celda / 10
    paso_fino = paso_fino or celda / 50
    filas = []
    malla = np.arange(-celda / 2, celda / 2 + 1e-9, paso_grueso)
    for nom in INTERP:
        for dx in malla:
            for dy in malla:
                c, n = costo(fun[nom](X + dx, Y + dy), ref, afin)
                filas.append(dict(interp=nom, dx=dx, dy=dy, costo=c, n=n, etapa="grueso"))
    # refinar alrededor del mejor de cada interpolador
    for nom in INTERP:
        b = min((f for f in filas if f["interp"] == nom), key=lambda f: f["costo"])
        fina = np.arange(-paso_grueso, paso_grueso + 1e-9, paso_fino)
        for ddx in fina:
            for ddy in fina:
                dx, dy = b["dx"] + ddx, b["dy"] + ddy
                c, n = costo(fun[nom](X + dx, Y + dy), ref, afin)
                filas.append(dict(interp=nom, dx=dx, dy=dy, costo=c, n=n, etapa="fino"))
    mejor_por = {nom: min((f for f in filas if f["interp"] == nom), key=lambda f: f["costo"]) for nom in INTERP}
    orden = sorted(mejor_por.values(), key=lambda f: f["costo"])
    res = dict(mejor=orden[0], segundo=orden[1], margen=orden[1]["costo"] / max(orden[0]["costo"], 1e-30),
               por_interp=mejor_por, borde=(abs(orden[0]["dx"]) >= celda / 2 - 1e-6 or
                                            abs(orden[0]["dy"]) >= celda / 2 - 1e-6))
    return filas, res


def leer_tif(ruta):
    import rasterio
    with rasterio.open(ruta) as s:
        epsg = s.crs.to_epsg()
        if epsg == 4326:
            raise SystemExit("TIF en EPSG:4326: fuera de la ventana UTM de A106, no sirve para la grilla")
        t = s.transform
        if abs(t.b) > 1e-9 or abs(t.d) > 1e-9 or abs(abs(t.a) - abs(t.e)) > 1e-6:
            raise SystemExit("TIF con rotacion o celda no cuadrada: fuera del supuesto")
        return s.read(1).astype(float), t.c, t.f, t.a, epsg


def main(npz, tif, afin=True):
    from pyproj import Transformer
    ref, ulx, uly, celda, epsg = leer_tif(tif)
    d = np.load(npz)
    lat, lon, val = (np.asarray(d[k], float).ravel() for k in ("lat", "lon", "val"))
    x, y = Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
    x, y = np.asarray(x), np.asarray(y)
    alto, ancho = ref.shape
    marg = 3 * celda + 2000
    sel = ((x > ulx - marg) & (x < ulx + ancho * celda + marg) & (y < uly + marg) & (y > uly - alto * celda - marg)
           & np.isfinite(val))
    print(f"muestras del granulo dentro del TIF (+ margen): {int(sel.sum())}")
    if sel.sum() < 500:
        raise SystemExit("muy pocas muestras: el granulo no cubre el TIF (SIN DATO, no falla del ajuste)")
    filas, res = ajustar(x[sel], y[sel], val[sel], ref, ulx, uly, celda, afin=afin)
    for k in ("mejor", "segundo"):
        f = res[k]
        print(f"{k}: {f['interp']} dx {f['dx']:+.1f} m dy {f['dy']:+.1f} m costo {f['costo']:.4f} n {f['n']}")
    print(f"margen segundo/mejor: {res['margen']:.3f} | mejor en el borde de la busqueda: {res['borde']}")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main(sys.argv[1], sys.argv[2], afin="--sin-afin" not in sys.argv)
