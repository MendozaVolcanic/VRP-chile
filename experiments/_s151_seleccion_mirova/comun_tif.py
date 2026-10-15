# -*- coding: utf-8 -*-
"""Piezas comunes del estudio de la tarea 1.4: que objeto informa MIROVA cuando hay calor lejos del crater.

POR QUE ESTE MODULO. El CSV de MIROVA trae una distancia sin acimut (`Distancia_km`, medida desde el centro de su
grilla, D15) y por eso no dice DONDE estaba el objeto. El GeoTIFF que MIROVA publica de cada pasada si lo dice:
es el campo de radiancia del infrarrojo medio de la escena (no VRP sumable, A24). Aca vive una sola definicion de
como se baja, se fecha, se lee y se mide ese TIF, para que los dos scripts del estudio usen la misma.

LAS CUATRO TRAMPAS YA PAGADAS (A106, A109, A24, A143):
  1. La hora del nombre del archivo no siempre es la de la pasada: se usa SOLO `acquisition_utc` del indice, y
     un archivo cuyo md5 aparece tambien con OTRA hora de adquisicion (MIROVA sirvio una imagen vieja bajo una
     hora nueva) queda fuera como ambiguo.
  2. El CRS cambia (ocho adquisiciones UTM el 14 y 15 de septiembre, EPSG:4326 el resto): se lee de cada archivo
     y las coordenadas de cada celda se transforman a lat/lon.
  3. El TIF no es VRP por pixel sumable (A24). Lo que se usa es el EXCESO LOCAL: el campo menos su mediana movil
     (paso alto, S139), que borra el gradiente topografico de A69 y deja los focos de uno o dos pixeles. La
     "energia" del foco es ese exceso por el coeficiente de Wooster del sensor: una aproximacion, y el estudio la
     contrasta contra el VRP que MIROVA publica antes de usarla (control que puede fallar).
  4. Nunca se hace pull ni clone del repo de TIF (17 GB): el indice y cada TIF se bajan por raw.githubusercontent,
     fijados al commit del indice, a un cache FUERA del repositorio (variable VRP_TIF_CACHE).
"""
from __future__ import annotations

import hashlib
import math
import os
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import rasterio.errors
from rasterio.warp import transform as rio_transform
from scipy.ndimage import binary_erosion, median_filter

# Ultimo commit que toco index.csv del archivo de TIF (consultado por la API el 2026-10-14). Desde el
# 2026-09-22 11:02 UTC el indice no crece: MIROVA dejo de actualizar sus GeoTIFF (HEAD del 2026-10-14 al TIF de
# Lascar VIIRS 375: Last-Modified 2026-09-22 10:26 GMT), aunque el poller sigue guardando las laminas PNG.
TIF_SHA = "3660cdfa77bdb177ce7de7f2743a1161f0736ef7"
RAW = f"https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/{TIF_SHA}/"
CACHE = Path(os.environ.get("VRP_TIF_CACHE", str(Path(tempfile.gettempdir()) / "vrp_tif_cache_s151")))
ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}

PX_KM = {"VIIRS375": 0.375, "VIIRS750": 0.75, "MODIS": 1.0}
# Paso alto: ventana de unos 3,4 a 5 km, mucho menor que el gradiente topografico y mayor que un foco (S139 uso 9 px
# en VIIRS 375 y mostro que el resultado no depende de la ventana).
KERNEL = {"VIIRS375": 9, "VIIRS750": 5, "MODIS": 5}
# Coeficiente de Wooster por pixel de area nadir (CLAUDE.md del proyecto, calibrado S14): VRP [W] = K x exceso
# de radiancia [W m-2 sr-1 um-1].
K_WOOSTER_W = {"VIIRS375": 18.0 * 140625.0, "VIIRS750": 19.7 * 562500.0, "MODIS": 18.9 * 1.0e6}
# Tolerancias en km, del orden de dos pixeles del sensor: la distancia de MIROVA esta cuantizada a la celda (D15)
# y su origen es un nodo de la grilla, que puede no coincidir con el centro del raster en una fraccion de pixel.
TOL_ANILLO_KM = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 2.0}
R_CRATER_KM = {"VIIRS375": 1.5, "VIIRS750": 2.0, "MODIS": 2.5}
COINCIDE_KM = {"VIIRS375": 1.0, "VIIRS750": 1.5, "MODIS": 2.0}


def km_xy(lat, lon, lat0, lon0):
    """Coordenadas planas locales (km) de (lat, lon) respecto de (lat0, lon0): basta para escenas de 50 km."""
    x = (np.asarray(lon) - lon0) * 111.320 * math.cos(math.radians(lat0))
    y = (np.asarray(lat) - lat0) * 110.574
    return x, y


def dist_km(lat1, lon1, lat2, lon2):
    x, y = km_xy(lat1, lon1, lat2, lon2)
    return np.hypot(x, y)


def _bajar(url, destino, md5=None):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        urllib.request.urlretrieve(url, destino)
    if md5 is not None and hashlib.md5(destino.read_bytes()).hexdigest() != md5:
        destino.unlink()
        return False
    return True


def indice():
    """Indice de TIF fijado por commit, con el nombre de volcan del proyecto y la marca de md5 ambiguo."""
    p = CACHE / f"index_{TIF_SHA[:10]}.csv"
    _bajar(RAW + "index.csv", p)
    ix = pd.read_csv(p)
    ix["vol"] = ix.volcano.map(lambda v: ARCH2OURS.get(v, v))
    ix["acq"] = pd.to_datetime(ix.acquisition_utc, utc=True, errors="coerce")
    con = ix.dropna(subset=["acq"])
    spread = con.groupby(["vol", "sensor", "md5"]).acq.agg(lambda s: (s.max() - s.min()).total_seconds())
    ambiguos = set(spread[spread > 120].index)
    ix["md5_ambiguo"] = [(v, s, m) in ambiguos for v, s, m in zip(ix.vol, ix.sensor, ix.md5)]
    return ix


def tif_de_pasada(ix_vs, t):
    """Fila del indice de la MISMA pasada (adquisicion a +-120 s). Devuelve (fila o None, motivo)."""
    if ix_vs is None or ix_vs.empty:
        return None, "sin_tif"
    c = ix_vs[(ix_vs.acq - t).abs().dt.total_seconds() <= 120]
    if c.empty:
        return None, "sin_tif"
    ok = c[~c.md5_ambiguo]
    if ok.empty:
        return None, "md5_ambiguo"
    ok = ok.sort_values("captured_at_utc")
    return ok.iloc[0], ("varias_versiones" if ok.md5.nunique() > 1 else "ok")


def ruta_tif(fila):
    return CACHE / fila.tif_path


def bajar_tif(fila):
    return _bajar(RAW + fila.tif_path, ruta_tif(fila), fila.md5)


def leer(path, sensor):
    """Raster, lat/lon de cada celda, centro del raster y campo de exceso local en desvios robustos.

    None si el archivo no es un TIF legible (MIROVA llego a servir respuestas truncadas; el poller las rechaza
    desde el 2026-09-19, Mirova tif-archive #3) o si tiene menos de 200 celdas validas."""
    try:
        s0 = rasterio.open(path)
    except rasterio.errors.RasterioIOError:
        return None
    with s0 as s:
        a = s.read(1).astype("float64")
        h, w = a.shape
        rows, cols = np.mgrid[0:h, 0:w]
        xs, ys = rasterio.transform.xy(s.transform, rows.ravel(), cols.ravel())
        xs, ys = np.asarray(xs), np.asarray(ys)
        crs = s.crs
        if not crs.is_geographic:
            xs, ys = rio_transform(crs, "EPSG:4326", list(xs), list(ys))
            xs, ys = np.asarray(xs), np.asarray(ys)
        lon, lat = xs.reshape(h, w), ys.reshape(h, w)
    fin = np.isfinite(a) & (a > 0)
    if fin.sum() < 200:
        return None
    b = np.where(fin, a, np.nanmedian(a[fin]))
    hp = b - median_filter(b, size=KERNEL[sensor])
    hp[~fin] = np.nan
    med = np.nanmedian(hp)
    sig = 1.4826 * np.nanmedian(np.abs(hp - med))
    if not np.isfinite(sig) or sig <= 0:
        return None
    # Donde se buscan focos: lejos del borde del raster y de los huecos sin dato. Ahi la mediana movil se calcula
    # con relleno y el "exceso" puede ser un artefacto (la primera corrida puso tres focos lejanos exactamente en la
    # esquina del raster; cambio hecho despues de verla, dicho).
    m = KERNEL[sensor] // 2
    buscable = binary_erosion(fin, iterations=2)
    buscable[:m, :] = buscable[-m:, :] = buscable[:, :m] = buscable[:, -m:] = False
    return {"a": a, "hp": hp, "z": (hp - med) / sig, "sig": float(sig), "lat": lat, "lon": lon,
            # centro del raster = punto medio de los centros de celda extremos (el centro de la grilla de MIROVA)
            "clat": float((lat.max() + lat.min()) / 2), "clon": float((lon.max() + lon.min()) / 2),
            "crs": str(crs), "fin": fin, "buscable": buscable, "sensor": sensor}


# Longitud de onda central de la banda del TIF (README del archivo de TIF: I04, M13, B21), para invertir Planck.
LAMBDA_UM = {"VIIRS375": 3.74, "VIIRS750": 4.05, "MODIS": 3.959}
_C1, _C2 = 1.191042e8, 1.4387752e4


def bt_k(L, sensor):
    """Temperatura de brillo de una radiancia espectral (W m-2 sr-1 um-1) en la banda MIR del sensor."""
    lam = LAMBDA_UM[sensor]
    return _C2 / (lam * math.log(1.0 + _C1 / (lam ** 5 * L))) if L and L > 0 and np.isfinite(L) else float("nan")


def dbt_mediana(R, pixeles):
    """Mediana de |BT del TIF - BT de nuestro pixel| (mejor celda 3x3) sobre nuestros pixeles dentro del raster.

    Es el control de que el TIF es de la MISMA pasada que nuestro record (A106: la hora puede mentir): si es el
    mismo granulo, las dos temperaturas coinciden en fracciones de kelvin (S147 midio 0,2 K); si es otra pasada,
    difieren en kelvin. Devuelve (mediana, n)."""
    d = []
    h, w = R["a"].shape
    for p in pixeles:
        if p.get("bt_k") is None:
            continue
        rc = celda(R, p["lat"], p["lon"])
        if rc is None or not R["fin"][rc]:
            continue
        # la grilla de MIROVA esta remuestreada (D17): el pixel nuestro puede caer en la celda vecina. Se toma la
        # celda de la ventana 3x3 con la BT mas parecida; el nulo (pixeles de otra pasada) pasa por lo mismo.
        r0, c0 = rc
        mejores = []
        for r in range(max(0, r0 - 1), min(h, r0 + 2)):
            for c in range(max(0, c0 - 1), min(w, c0 + 2)):
                if R["fin"][r, c]:
                    mejores.append(bt_k(float(R["a"][r, c]), R["sensor"]) - float(p["bt_k"]))
        d.append(min(mejores, key=abs))
    return (float(np.median(np.abs(d))), len(d)) if d else (None, 0)


def energia_mw(R, r, c):
    """Exceso local positivo en la ventana 3x3 del foco, por el coeficiente de Wooster (aproximacion, A24)."""
    h, w = R["hp"].shape
    win = R["hp"][max(0, r - 1):min(h, r + 2), max(0, c - 1):min(w, c + 2)]
    return float(np.nansum(np.clip(win, 0, None)) * K_WOOSTER_W[R["sensor"]] / 1e6)


def foco_en(R, mascara):
    """Maximo del exceso local (en desvios robustos) dentro de la mascara: (z, r, c) o None."""
    m = mascara & R["buscable"]
    if not m.any():
        return None
    zz = np.where(m, R["z"], -np.inf)
    k = int(np.argmax(zz))
    r, c = np.unravel_index(k, zz.shape)
    return float(zz[r, c]), int(r), int(c)


def dist_desde(R, lat0, lon0):
    return dist_km(R["lat"], R["lon"], lat0, lon0)


def rotar(lat, lon, lat0, lon0, ang_deg):
    """Punto a la misma distancia de (lat0, lon0) que (lat, lon), girado ang_deg grados."""
    x, y = km_xy(lat, lon, lat0, lon0)
    t = math.radians(ang_deg)
    xr, yr = x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)
    return lat0 + yr / 110.574, lon0 + xr / (111.320 * math.cos(math.radians(lat0)))


def celda(R, lat, lon):
    """Celda mas cercana a (lat, lon) si cae dentro del raster (a menos de un pixel), si no None."""
    d = dist_km(R["lat"], R["lon"], lat, lon)
    k = int(np.argmin(d))
    r, c = np.unravel_index(k, d.shape)
    return (int(r), int(c)) if d[r, c] <= PX_KM[R["sensor"]] else None
