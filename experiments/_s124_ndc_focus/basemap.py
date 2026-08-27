# -*- coding: utf-8 -*-
"""Fondo satelital para los mapas locales en km (S124).

POR QUÉ: un mapa de puntos sobre grilla vacía no deja juzgar si una detección
cae sobre el cráter, sobre el glaciar o sobre el valle. Con la imagen debajo,
la posición de cada anomalía se lee contra el terreno real.

Fuente: ESRI World Imagery (teselas públicas). Se cachean en disco para no
volver a pedirlas en cada corrida.

Nota de proyección: las teselas son Web Mercator; el mapa usa un marco local
plano en km centrado en el cráter. Sobre una ventana de ~11 km la diferencia
entre ambos es <0,1 % (muy por debajo de un píxel de la figura), así que basta
con convertir las esquinas del mosaico y estirar la imagen a ese extent.
"""
from __future__ import annotations

import io
import math
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

TILE = 256
URL = ("https://server.arcgisonline.com/ArcGIS/rest/services/"
       "World_Imagery/MapServer/tile/{z}/{y}/{x}")
ATRIBUCION = "Imagen: ESRI World Imagery"
CACHE = Path(__file__).parent / "_tiles_cache"


def _deg2tile(lat, lon, z):
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n
    return x, y


def _tile2deg(x, y, z):
    n = 2.0 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def _fetch(z, x, y):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{z}_{x}_{y}.jpg"
    if f.exists():
        return Image.open(f).convert("RGB")
    req = urllib.request.Request(URL.format(z=z, x=x, y=y),
                                 headers={"User-Agent": "VRP-Chile/monitoreo"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    f.write_bytes(raw)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def satelital_km(center_lat, center_lon, half_km, zoom=14):
    """Mosaico satelital cubriendo ±half_km del centro.

    Returns:
        (imagen RGB como array, extent [x0,x1,y0,y1] en km locales) — listo
        para `ax.imshow(img, extent=extent)`. Si la descarga falla devuelve
        (None, None): el mapa se dibuja igual, sin fondo.
    """
    # margen del 12 % para que el mosaico sobre y no queden bordes blancos
    d = half_km * 1.12
    dlat = d / 111.32
    dlon = d / (111.32 * math.cos(math.radians(center_lat)))
    lat_n, lat_s = center_lat + dlat, center_lat - dlat
    lon_w, lon_e = center_lon - dlon, center_lon + dlon

    x0f, y0f = _deg2tile(lat_n, lon_w, zoom)
    x1f, y1f = _deg2tile(lat_s, lon_e, zoom)
    x0, y0 = int(math.floor(x0f)), int(math.floor(y0f))
    x1, y1 = int(math.floor(x1f)), int(math.floor(y1f))

    ancho, alto = (x1 - x0 + 1), (y1 - y0 + 1)
    if ancho * alto > 400:
        raise ValueError(f"mosaico demasiado grande ({ancho}x{alto} teselas)")

    mosaico = Image.new("RGB", (ancho * TILE, alto * TILE))
    try:
        for i, tx in enumerate(range(x0, x1 + 1)):
            for j, ty in enumerate(range(y0, y1 + 1)):
                mosaico.paste(_fetch(zoom, tx, ty), (i * TILE, j * TILE))
    except Exception as e:                      # sin red / tesela faltante
        print(f"  [basemap] sin fondo satelital: {type(e).__name__}: {e}")
        return None, None

    # esquinas exactas del mosaico -> km locales
    lat_top, lon_left = _tile2deg(x0, y0, zoom)
    lat_bot, lon_right = _tile2deg(x1 + 1, y1 + 1, zoom)
    kx = 111.32 * math.cos(math.radians(center_lat))
    extent = [(lon_left - center_lon) * kx, (lon_right - center_lon) * kx,
              (lat_bot - center_lat) * 111.32, (lat_top - center_lat) * 111.32]
    return np.asarray(mosaico), extent
