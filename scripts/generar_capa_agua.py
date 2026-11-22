# -*- coding: utf-8 -*-
"""S193: capa de cuerpos de agua del tablero, un GeoJSON liviano por volcán (frontend/agua/<Volcan>.geojson).

POR QUÉ. De noche un lago guarda el calor del día y queda más tibio que la roca y la nieve que lo rodean: para el
detector es un conjunto de píxeles más tibios que sus vecinos, que es lo que busca. Coppola et al. 2016a
(documentacion/sp426_5.txt, l. 689 a 694) lo reconoce: falsas detecciones de menos de 5 MW en el borde de cuerpos de
agua, que el operador quita mirando el mapa. La sesión S193 «lagos» (experiments/_s193_lagos/INFORME.md) midió que el
píxel más caliente cae sobre agua en 124 de 14.391 pasadas con detección de la vía (0,9 %), con Laguna del Maule y
Carrán-Los Venados a la cabeza. El tablero no tenía cómo mostrarlo: el revisor veía el punto sobre una imagen
satelital donde un lago de noche no se distingue. Esta capa sólo se dibuja; no cambia ninguna detección ni ningún
valor publicado (la producción, como MIROVA, no tiene máscara de agua).

FUENTE Y CRITERIO, los mismos de experiments/_s193_lagos/medir_agua.py para que el tablero y el informe digan lo mismo:
JRC Global Surface Water v1.4 (Pekel et al. 2016, Nature 540), capa `occurrence` 1984 a 2021, 30 m (0,00025°),
leída de storage.googleapis.com/global-surface-water. Es agua toda celda JRC con ocurrencia de 50 % o más (agua
permanente o casi). Incluye lagos, embalses, mar y fiordos. Es un promedio de 37 años: no sabe si esa noche el lago
estaba congelado.

GEOMETRÍA. Se poligoniza la máscara a 30 m (4-conexo), se simplifica con tolerancia TOL_GRADOS (menos de un píxel
JRC, sólo quita la escalera del raster) y se descartan los polígonos de menos de AREA_MIN_KM2 (charcos que no llenan
ni la décima parte de una celda de 375 m). Ventana: ±MEDIA_VENTANA_KM alrededor del punto del volcán, que cubre la
grilla de 51 × 51 km de la vía con su celda más grande (1 km) en el borde. Coordenadas con 5 decimales (~1 m).
El tablero calcula la fracción de agua de una celda recortando estos polígonos (frontend/agua.js); cuánto se aparta
de la máscara a 30 m está medido en experiments/_s193_mapas_agua/comparar_fraccion.py.

Uso:
  python scripts/generar_capa_agua.py <dir_cache_jrc> [Volcan ...]
El caché guarda la ventana JRC de cada volcán (npz); si falta, se baja. Escribe frontend/agua/<Volcan>.geojson.
"""
import json
import math
import os
import sys

import numpy as np
import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "frontend", "agua")

UMBRAL_OCURRENCIA = 50
RES = 0.00025                 # paso de JRC (grados)
MEDIA_VENTANA_KM = 30.0
TOL_GRADOS = 0.0004           # ~1,6 píxeles JRC: quita la escalera del raster; medido en experiments/_s193_mapas_agua
AREA_MIN_KM2 = 0.015
DECIMALES = 5
VERSION = "JRC GSW v1.4 occurrence 1984-2021, >= 50 %"


def tile_url(lat, lon):
    """Teselas de 10° de JRC, nombradas por su esquina noroeste (copia de medir_agua.py)."""
    lon0 = int(math.floor(lon / 10.0) * 10)
    lat0 = int(math.ceil(lat / 10.0) * 10)
    lon_s = f"{abs(lon0)}{'W' if lon0 < 0 else 'E'}"
    lat_s = f"{abs(lat0)}{'S' if lat0 <= 0 else 'N'}" if lat0 != 0 else "0N"
    return ("/vsicurl/https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/"
            f"occurrence_{lon_s}_{lat_s}v1_4_2021.tif")


def ventana_jrc(cache, nombre, lat, lon, dlat=0.36):
    """Ventana JRC de ±0,36° de latitud (la misma de medir_agua.py, así reusa su caché)."""
    f = os.path.join(cache, f"{nombre}.npz")
    if os.path.exists(f):
        z = np.load(f)
        return z["a"], tuple(z["t"])
    import rasterio
    from rasterio.windows import from_bounds
    dlon = dlat / math.cos(math.radians(lat))
    W, S, E, N = lon - dlon, lat - dlat, lon + dlon, lat + dlat
    nx = int(round((E - W) / RES)); ny = int(round((N - S) / RES))
    a = np.full((ny, nx), 255, dtype=np.uint8)
    urls = {tile_url(la, lo) for la in (S + 1e-6, N - 1e-6) for lo in (W + 1e-6, E - 1e-6)}
    for u in urls:
        with rasterio.open(u) as ds:
            tb = ds.bounds
            iw, is_, ie, in_ = max(W, tb.left), max(S, tb.bottom), min(E, tb.right), min(N, tb.top)
            if iw >= ie or is_ >= in_:
                continue
            win = from_bounds(iw, is_, ie, in_, ds.transform)
            sub = ds.read(1, window=win, boundless=True, fill_value=255)
            c0 = int(round((iw - W) / RES)); r0 = int(round((N - in_) / RES))
            h, w = sub.shape
            h = min(h, ny - r0); w = min(w, nx - c0)
            a[r0:r0 + h, c0:c0 + w] = sub[:h, :w]
    t = (W, N, RES)
    os.makedirs(cache, exist_ok=True)
    np.savez_compressed(f, a=a, t=np.array(t))
    return a, t


def poligonos(a, t, lat, lon, tol=None, area_min_km2=None):
    """Polígonos de agua (shapely) dentro de ±MEDIA_VENTANA_KM del punto."""
    tol = TOL_GRADOS if tol is None else tol
    area_min_km2 = AREA_MIN_KM2 if area_min_km2 is None else area_min_km2
    from affine import Affine
    from rasterio import features
    from shapely.geometry import box, shape
    W, N, res = t
    agua = ((a >= UMBRAL_OCURRENCIA) & (a <= 100)).astype(np.uint8)
    tr = Affine(res, 0, W, 0, -res, N)
    dlat = MEDIA_VENTANA_KM / 111.32
    dlon = MEDIA_VENTANA_KM / (111.32 * math.cos(math.radians(lat)))
    marco = box(lon - dlon, lat - dlat, lon + dlon, lat + dlat)
    km2_por_grado2 = 111.32 * 111.32 * math.cos(math.radians(lat))
    out = []
    for geom, val in features.shapes(agua, mask=agua.astype(bool), transform=tr, connectivity=4):
        if val != 1:
            continue
        g = shape(geom)
        if not g.intersects(marco):
            continue
        g = g.intersection(marco)
        if tol:
            g = g.simplify(tol, preserve_topology=True)
        partes = list(g.geoms) if hasattr(g, "geoms") else [g]
        for p in partes:
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            if p.area * km2_por_grado2 < area_min_km2:
                continue
            out.append(p)
    return out


def a_geojson(polys, nombre, lat, lon):
    def anillo(c):
        return [[round(x, DECIMALES), round(y, DECIMALES)] for x, y in c]
    feats = []
    for p in polys:
        coords = [anillo(p.exterior.coords)] + [anillo(i.coords) for i in p.interiors]
        feats.append({"type": "Feature", "properties": {},
                      "geometry": {"type": "Polygon", "coordinates": coords}})
    return {"type": "FeatureCollection",
            "properties": {"volcan": nombre, "lat": lat, "lon": lon, "fuente": VERSION,
                           "umbral_ocurrencia_pct": UMBRAL_OCURRENCIA, "media_ventana_km": MEDIA_VENTANA_KM,
                           "tolerancia_grados": TOL_GRADOS, "area_min_km2": AREA_MIN_KM2,
                           "generador": "scripts/generar_capa_agua.py"},
            "features": feats}


def volcanes():
    with open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8") as fh:
        vy = yaml.safe_load(fh)
    vs = vy["volcanoes"] if isinstance(vy, dict) else vy
    return [v for v in vs if v.get("active", True) is not False]


def main():
    cache = sys.argv[1]
    pedidos = set(sys.argv[2:])
    os.makedirs(SALIDA, exist_ok=True)
    total = 0
    for v in volcanes():
        nombre, lat, lon = v["name"], float(v["lat"]), float(v["lon"])
        if pedidos and nombre not in pedidos:
            continue
        a, t = ventana_jrc(cache, nombre, lat, lon)
        gj = a_geojson(poligonos(a, t, lat, lon), nombre, lat, lon)
        f = os.path.join(SALIDA, f"{nombre}.geojson")
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(gj, fh, ensure_ascii=False, separators=(",", ":"))
            fh.write("\n")
        kb = os.path.getsize(f) / 1024
        total += kb
        print(f"{nombre}: {len(gj['features'])} polígonos, {kb:.0f} KB", flush=True)
    print(f"total {total:.0f} KB")


if __name__ == "__main__":
    main()
