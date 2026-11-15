# FICHA (SDA, CPLT 372): experimento de sensibilidad, NO es detección de producción. No escribe en data/ ni cambia ningún
# flag; solo lee L1B y calcula variantes del remuestreo de la vía «código MIROVA».
"""Interpoladores alternativos al `remuestrear_grilla` de la vía, con la MISMA firma, para el A/B local (no toca pipeline/).

POR QUÉ: el informe s185_tupungatito_6 deja como SOSPECHA que MIROVA remuestrea distinto del `griddata` lineal de la vía:
con el lineal, el calor de un píxel aislado se reparte entre las celdas vecinas. Estas variantes miden cuánto cambia la
decisión (Tupungatito V750) o la magnitud (Chillán V375) con otro remuestreo. Ninguna es «la de MIROVA» (no está
publicada): son sondas de sensibilidad.

Variantes:
  lineal      el de producción (pipeline.mirova_v750_codigo.remuestrear_grilla).
  vecino      griddata method=nearest.
  promedio    promedio de los píxeles nativos cuyo centro cae en cada celda; celdas vacías = valor del vecino más cercano.
  desp_*      el lineal de producción, pero con la grilla corrida media celda (se aplica a la grilla, no al interpolador).
"""
import numpy as np

RADIO_RECORTE_KM = 45.0   # el mismo recorte de la vía (probe_n.grillar)


def _xy_recortados(lat, lon, grilla, radio_km=RADIO_RECORTE_KM):
    from pyproj import Transformer
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    dlat, dlon = np.radians(lat - grilla["centro_lat"]), np.radians(lon - grilla["centro_lon"])
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat)) * np.cos(np.radians(grilla["centro_lat"])) * np.sin(dlon / 2) ** 2)
    with np.errstate(invalid="ignore"):
        sel = np.isfinite(lat) & (6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) < radio_km)
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    x, y = t.transform(lon[sel], lat[sel])
    return sel, x, y


def _centros(grilla):
    n, paso = int(grilla["n"]), float(grilla["paso"])
    return np.meshgrid(grilla["ul_x"] + paso * (np.arange(n) + 0.5), grilla["ul_y"] - paso * (np.arange(n) + 0.5))


def celdas_de(grilla, lat, lon):
    """Versión vectorizada de MV.celda_de (misma regla, un solo transformador): (fila, col) enteros por punto."""
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    x, y = t.transform(np.asarray(lon, float), np.asarray(lat, float))
    paso = float(grilla["paso"])
    return np.floor((grilla["ul_y"] - y) / paso).astype(int), np.floor((x - grilla["ul_x"]) / paso).astype(int)


def vecino(lat, lon, m13, m15, grilla, radio_km=RADIO_RECORTE_KM):
    from scipy.interpolate import griddata
    sel, x, y = _xy_recortados(lat, lon, grilla, radio_km)
    X, Y = _centros(grilla)
    out = []
    for v in (np.asarray(m13, float)[sel], np.asarray(m15, float)[sel]):
        ok = np.isfinite(v)
        out.append(griddata(np.column_stack([x[ok], y[ok]]), v[ok], (X, Y), method="nearest"))
    return tuple(out)


def promedio(lat, lon, m13, m15, grilla, radio_km=RADIO_RECORTE_KM):
    from scipy.interpolate import griddata
    sel, x, y = _xy_recortados(lat, lon, grilla, radio_km)
    n, paso = int(grilla["n"]), float(grilla["paso"])
    ix = np.floor((x - grilla["ul_x"]) / paso).astype(int)
    iy = np.floor((grilla["ul_y"] - y) / paso).astype(int)
    dentro = (ix >= 0) & (ix < n) & (iy >= 0) & (iy < n)
    X, Y = _centros(grilla)
    out = []
    for v in (np.asarray(m13, float)[sel], np.asarray(m15, float)[sel]):
        fin = np.isfinite(v)
        ok = fin & dentro
        s = np.zeros((n, n))
        c = np.zeros((n, n))
        np.add.at(s, (iy[ok], ix[ok]), v[ok])
        np.add.at(c, (iy[ok], ix[ok]), 1.0)
        g = np.where(c > 0, s / np.maximum(c, 1), np.nan)
        vacias = np.isnan(g)
        if vacias.any():
            relleno = griddata(np.column_stack([x[fin], y[fin]]), v[fin], (X, Y), method="nearest")
            g[vacias] = relleno[vacias]
        out.append(g)
    return tuple(out)


def grilla_desplazada(grilla, dx_m, dy_m):
    """Copia de la grilla con la esquina superior izquierda corrida (dx_m hacia el este, dy_m hacia el norte). Todo lo que
    depende de la grilla (celda del cráter, caja) se recalcula solo, porque calcular_vrp_granulo lee la grilla que recibe."""
    g = dict(grilla)
    g["ul_x"] = grilla["ul_x"] + dx_m
    g["ul_y"] = grilla["ul_y"] + dy_m
    return g


DESPLAZAMIENTOS = {"desp_E": (0.5, 0.0), "desp_O": (-0.5, 0.0), "desp_N": (0.0, 0.5), "desp_S": (0.0, -0.5)}  # en celdas
