# -*- coding: utf-8 -*-
"""F2 · descarga y lectura de un GeoTIFF de MIROVA (solo POSICION, nunca magnitud - A24)."""
import os, urllib.request, math
import numpy as np
import f2_common as F

DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tif")
BASE = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"

def bajar(tif_path):
    dst = os.path.join(DEST, tif_path.replace("/", "__"))
    os.makedirs(DEST, exist_ok=True)
    if not os.path.exists(dst) or os.path.getsize(dst) == 0:
        urllib.request.urlretrieve(BASE + tif_path, dst)
    return dst

def leer(tif_path):
    """Devuelve (arr, lats, lons) - grillas 2D de coordenadas por celda (centro)."""
    import rasterio
    p = bajar(tif_path)
    with rasterio.open(p) as ds:
        arr = ds.read(1).astype("float64")
        if ds.nodata is not None:
            arr = np.where(arr == ds.nodata, np.nan, arr)
        T = ds.transform
        crs = str(ds.crs)
        ny, nx = arr.shape
        j, i = np.meshgrid(np.arange(nx), np.arange(ny))
        xs, ys = rasterio.transform.xy(T, i, j, offset="center")
        xs = np.array(xs); ys = np.array(ys)
        if ds.crs and not ds.crs.is_geographic:
            from rasterio.warp import transform as wtr
            lon, lat = wtr(ds.crs, "EPSG:4326", xs.ravel(), ys.ravel())
            lons = np.array(lon).reshape(arr.shape); lats = np.array(lat).reshape(arr.shape)
        else:
            lons, lats = xs, ys
    return arr, lats, lons, crs

def semiancho_km(lats, lons, clat, clon):
    """Distancia del centro del raster a su esquina, en km, por eje (control de georref)."""
    ny, nx = lats.shape
    dy = F.haversine(lats[0, nx//2], lons[0, nx//2], lats[-1, nx//2], lons[-1, nx//2]) / 2
    dx = F.haversine(lats[ny//2, 0], lons[ny//2, 0], lats[ny//2, -1], lons[ny//2, -1]) / 2
    return dx, dy
