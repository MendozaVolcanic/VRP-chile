# -*- coding: utf-8 -*-
"""Piezas de la vía «código MIROVA» de MODIS (MOD-D, pipeline/mirova_v750_codigo.py) reemplazables de a una.

POR QUÉ. Cuando el satélite mira el domo de lado, el píxel nativo de MODIS crece (a 58° de cenit cubre del orden de 6
veces el suelo del nadir) y el calor de un foco pequeño queda repartido en ese píxel grande: el exceso de radiancia
por píxel baja en la misma proporción en que crece el píxel. K suma ese exceso con el área del nadir (1 km²) y por eso
su VRP cae con el cenit. La vía MOD-D, como MIROVA, interpola el gránulo a una grilla UTM fija de 1 km antes de
detectar: el píxel grande se copia en varias celdas, cada una se cuenta con 1 km², y la suma recupera el área. Esa es
la hipótesis de D17. La competidora es D25: el fondo que se resta (K: mediana de BT de un anillo de 5 a 25 km, con el
exceso recortado a cero; MOD-D: interpolación fillmissing2 bajo un halo de 3, 5 o 7 celdas, sin recorte). Las dos
viajan juntas en el paquete; este módulo las separa.

Cada brazo cambia UNA pieza de la vía y deja el resto como en producción (S172, flag enable_modis_codigo_mirova):
  V0         la vía tal cual (control: tiene que dar el record de la vía bit a bit)
  X2         control positivo: el coeficiente del VRP por 2 (la magnitud tiene que doblarse, la detección no cambiar)
  FA         D25: fondo de K (mediana de la BT MIR del anillo de 5 a 25 km del centro del volcán, en las celdas de la
             grilla; L_bg de esa mediana; exceso recortado a cero) sobre la máscara de la vía
  FSH        fondo de la vía sin el halo (fillmissing2 con sólo los alertados en NaN)
  SC         suma: sólo el cúmulo 8-conexo del alertado más radiante, con el fondo de la vía (K publica un cúmulo)
  FA_SC      FA y SC juntos (el fondo y la suma de K sobre la detección de la vía)
  RN         D17 a medias: remuestreo por vecino más cercano en vez de lineal (copia el píxel grande, sin suavizar)
  G5         geolocalización de 5 km interpolada (la de K) en vez del MxD03 de 1 km
  NAT        D17 entero: sin remuestreo; el detector, el fondo y la suma de la vía sobre los píxeles nativos, cada uno
             con el área del nadir (1 km²), como K
  NAT_AREA   diagnóstico físico, no es pieza de K: NAT con el área de cada píxel nativo (1/cos³ del cenit, la ley de
             scan_geometry.area_factor_from_zenith)
Lo que NO se puede reemplazar de a uno aquí: el detector de K (corre sobre el barrido nativo con su anillo y su
segundo pase; meterlo en la grilla es otro detector). D28 (bow tie) no es diferencia entre K y la vía: ninguno de los
dos quita duplicados (ver INFORME, VERIFICADO LIMPIO).

Sólo lectura: importa pipeline/ y lo llama; los reemplazos son funciones propias o patch.object dentro del proceso (A75).
"""
from __future__ import annotations

import math
from contextlib import ExitStack
from unittest.mock import patch

import numpy as np

from pipeline import mirova_v750_codigo as MV

FAM = MV.FAMILIAS["MODIS"]
_VRP_VIA = MV.vrp_mirova   # referencia al original: el patch reemplaza MV.vrp_mirova dentro de procesar_grilla
LAM = FAM["lam_mir"]
COEF = FAM["coef"]
BG_INNER_KM, BG_OUTER_KM = 5.0, 25.0   # pipeline/profile.py BG_INNER_KM / BG_OUTER_KM (se comprueba en la prueba)
BRAZOS_GRILLA = ("V0", "X2", "FA", "FSH", "SC", "FA_SC")
BRAZOS_NATIVOS = ("RN", "G5", "NAT", "NAT_AREA")
BRAZOS = BRAZOS_GRILLA + BRAZOS_NATIVOS


# ---------------------------------------------------------------------------------------------- fondos y sumas
def fondo_via(m13, mascara, halo=True):
    """Fondo de MIROVA_VIIRS750_VRP.m tal como lo porta vrp_mirova (l. 63-81), con o sin el halo dilatado."""
    from scipy.ndimage import binary_dilation
    enm = np.asarray(m13, float).copy()
    enm[mascara] = np.nan
    if halo:
        npix = int(mascara.sum())
        k = 3 if npix <= 4 else (5 if npix <= 30 else 7)
        excl = binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))
        enm[excl] = np.nan
    return MV._fillmissing2_lineal(enm)


def t_bg_anillo(m13, dist_km, excluir=None):
    """Mediana de la BT MIR (inversión de Planck de la vía) de las celdas a 5-25 km del centro del volcán: el t_bg de
    K (compute_bg_stats: mediana sobre el anillo, sin excluir alertados; process_modis.py:717 y detection_context.py:1042)."""
    bt = MV.radiancia_a_temperatura(np.asarray(m13, float), LAM)
    sel = (dist_km >= BG_INNER_KM) & (dist_km <= BG_OUTER_KM) & np.isfinite(bt)
    if excluir is not None:
        sel &= ~excluir
    return float(np.median(bt[sel])) if sel.sum() >= 10 else float("nan")


def vrp_desde(m13, mascara, fondo_L, coef=COEF, recortar=False, sumar=None):
    """VRP = coef x suma (L - L_bg) sobre `sumar` (por defecto toda la máscara)."""
    m13 = np.asarray(m13, float)
    mascara = np.asarray(mascara, bool)
    npix = int(mascara.sum())
    if npix == 0:
        return {"VRP_MW": np.nan, "npix": 0, "L_hot": np.nan, "L_bk": np.nan, "deltaL": np.nan}
    s = mascara if sumar is None else sumar
    Lb = fondo_L[s] if np.ndim(fondo_L) else np.full(int(s.sum()), float(fondo_L))
    dl = m13[s] - Lb
    if recortar:
        dl = np.maximum(dl, 0.0)
    L_hot = float(np.nansum(m13[s]))
    return {"VRP_MW": float(np.nansum(dl)) * coef, "npix": npix, "L_hot": L_hot, "L_bk": float(np.nansum(Lb)),
            "deltaL": float(np.nansum(dl))}


def cumulo(mascara, m13):
    c = np.zeros(mascara.shape, bool)
    if mascara.any():
        for a, b in MV._cumulo_del_mas_radiante(mascara, m13):
            c[a, b] = True
    return c


def dist_celdas_km(grilla, lat0, lon0):
    """Distancia (km) del centro de cada celda de la grilla al punto (lat0, lon0)."""
    from pyproj import Transformer
    n, paso = int(grilla["n"]), float(grilla["paso"])
    X, Y = np.meshgrid(grilla["ul_x"] + paso * (np.arange(n) + 0.5), grilla["ul_y"] - paso * (np.arange(n) + 0.5))
    t = Transformer.from_crs(f"EPSG:{grilla['epsg']}", "EPSG:4326", always_xy=True)
    lo, la = t.transform(X, Y)
    return MV._haversine(np.asarray(la), np.asarray(lo), lat0, lon0)


def vrp_de_brazo(brazo, dist_km=None):
    """Función con la firma de _VRP_VIA(m13, mascara, coef) para los brazos de grilla."""
    def f(m13, mascara, coef=COEF):
        m13 = np.asarray(m13, float)
        mascara = np.asarray(mascara, bool)
        if not mascara.any():
            return _VRP_VIA(m13, mascara, coef=coef)
        if brazo == "V0":
            return _VRP_VIA(m13, mascara, coef=coef)
        if brazo == "X2":
            return _VRP_VIA(m13, mascara, coef=2 * coef)
        sc = cumulo(mascara, m13) if brazo in ("SC", "FA_SC") else None
        if brazo in ("FA", "FA_SC"):
            tb = t_bg_anillo(m13, dist_km)
            Lb = float(MV.temperatura_a_radiancia(np.array([tb]), LAM)[0])
            return vrp_desde(m13, mascara, Lb, coef, recortar=True, sumar=sc)
        if brazo == "FSH":
            return vrp_desde(m13, mascara, fondo_via(m13, mascara, halo=False), coef)
        if brazo == "SC":
            return vrp_desde(m13, mascara, fondo_via(m13, mascara, halo=True), coef, sumar=sc)
        raise ValueError(brazo)
    return f


# ---------------------------------------------------------------------------------------------- grilla
def correr_en_grilla(brazo, mirg, tirg, grilla, box, dayflag, sunglint, pos_crater, inner_km, sensor, volcan_latlon):
    """Record de la vía (MV.procesar_grilla) con la pieza del brazo reemplazada por patch.object (sólo en el proceso).
    Para los brazos de grilla la detección es la de la vía; sólo cambia la magnitud."""
    dist = dist_celdas_km(grilla, *volcan_latlon) if brazo in ("FA", "FA_SC") else None
    with patch.object(MV, "vrp_mirova", vrp_de_brazo(brazo, dist)):
        return MV.procesar_grilla(mirg, tirg, grilla, box, dayflag, sunglint, pos_crater, inner_km, sensor,
                                  familia="MODIS")


def remuestrear_vecino(lat, lon, m13, m15, grilla, radio_km=MV.RADIO_RECORTE_KM):
    """Igual que MV.remuestrear_grilla pero con method='nearest' (dentro de la envolvente convexa, como el lineal)."""
    from pyproj import Transformer
    from scipy.interpolate import griddata
    lin = MV.remuestrear_grilla(lat, lon, m13, m15, grilla, radio_km)   # para copiar la máscara de la envolvente
    n, paso = int(grilla["n"]), float(grilla["paso"])
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    sel = np.isfinite(lat) & (MV._haversine(lat, lon, grilla["centro_lat"], grilla["centro_lon"]) < radio_km)
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    x, y = t.transform(lon[sel], lat[sel])
    X, Y = np.meshgrid(grilla["ul_x"] + paso * (np.arange(n) + 0.5), grilla["ul_y"] - paso * (np.arange(n) + 0.5))
    out = []
    for v, ref in zip((np.asarray(m13, float)[sel], np.asarray(m15, float)[sel]), lin):
        ok = np.isfinite(v)
        g = griddata(np.column_stack([x[ok], y[ok]]), v[ok], (X, Y), method="nearest")
        g[np.isnan(ref)] = np.nan
        out.append(g)
    return tuple(out)


def preparar_grilla(rad, lat, lon, grilla, vent_latlon, inner_km, remuestreo=None):
    """Los pasos de MV.calcular_vrp_granulo entre la lectura y procesar_grilla (rama MODIS): remuestreo, posición del
    cráter y caja. remuestreo: None = MV.remuestrear_grilla (lineal), o una función con la misma firma."""
    rem = remuestreo or MV.remuestrear_grilla
    m13g, m15g = rem(lat, lon, rad["MIR"], rad["TIR"], grilla)
    pos = MV.posicion_de(grilla, *vent_latlon)
    celda = MV.celda_de(grilla, *vent_latlon)
    box = MV.caja_roi(grilla.get("roi", "def"), n=grilla["n"], celda_crater=celda, inner_km=inner_km,
                      lado_sensible=FAM["lado_sensible"], lado_anillo=FAM["lado_anillo"], paso_m=grilla["paso"])
    return m13g, m15g, box, pos


def dayflag_sunglint(lat, lon, angulos, grilla):
    """dayflag y sun-glint como MV.calcular_vrp_granulo: geometría del píxel nativo más cercano al centro de la grilla."""
    dist = MV._haversine(np.asarray(lat, float), np.asarray(lon, float), grilla["centro_lat"], grilla["centro_lon"])
    sel = np.isfinite(dist) & (dist < MV.RADIO_RECORTE_KM)
    i0 = np.unravel_index(np.nanargmin(np.where(sel, dist, np.inf)), dist.shape)
    geom = {k: float(np.asarray(v)[i0]) for k, v in (angulos or {}).items() if v is not None}
    dayflag = 0 if geom.get("solar_zenith", 180.0) > 90 else 1
    sg = MV.sunglint_deg(geom.get("sensor_zenith", 0.0), geom.get("solar_zenith", 0.0),
                         geom.get("sensor_azimuth", 0.0), geom.get("solar_azimuth", 0.0))
    return dayflag, sg, geom, float(dist[i0])


# ---------------------------------------------------------------------------------------------- nativo (sin remuestreo)
def correr_nativo(rad, lat, lon, grilla, vent_latlon, inner_km, dayflag, sunglint, sensor_zenith=None, area_real=False):
    """NAT / NAT_AREA: el detector, el fondo y la suma de la vía sobre los píxeles NATIVOS (sin remuestrear).

    La zona de cada píxel nativo (sensible, conservadora, fuera) es la de la celda de la grilla de MIROVA en que cae su
    centro; los que caen fuera del cuadrado de 51 km quedan excluidos (NaN en la caja), como fuera de la grilla. El
    promedio 3 x 3, la sigma global y el fillmissing2 corren sobre la matriz del barrido (vecinos del barrido). Área:
    1 km² por píxel (nadir fijo, la de K) o, con area_real, 1/cos³ del cenit del píxel."""
    from pyproj import Transformer
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    mir = np.asarray(rad["MIR"], float)
    tir = np.asarray(rad["TIR"], float)
    n, paso = int(grilla["n"]), float(grilla["paso"])
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{grilla['epsg']}", always_xy=True)
    ok = np.isfinite(lat) & np.isfinite(lon)
    x = np.full(lat.shape, np.nan)
    y = np.full(lat.shape, np.nan)
    x[ok], y[ok] = t.transform(lon[ok], lat[ok])
    with np.errstate(invalid="ignore"):
        fila = np.floor((grilla["ul_y"] - y) / paso)
        col = np.floor((x - grilla["ul_x"]) / paso)
    dentro = ok & (fila >= 0) & (fila < n) & (col >= 0) & (col < n)
    if not dentro.any():
        return {"npix": 0, "vrp_mw": None, "motivo": "fuera_de_la_grilla", "dist_min_cumulo_km": None, "n_dentro": 0}
    box_g = MV.caja_roi(grilla.get("roi", "def"), n=n, celda_crater=MV.celda_de(grilla, *vent_latlon),
                        inner_km=inner_km, lado_sensible=FAM["lado_sensible"], lado_anillo=FAM["lado_anillo"],
                        paso_m=paso)
    box = np.full(lat.shape, np.nan)
    box[dentro] = box_g[fila[dentro].astype(int), col[dentro].astype(int)]
    # recorte de la matriz nativa a la caja que contiene el cuadrado de 51 km (+2 píxeles); fuera del cuadrado los
    # píxeles conservan su radiancia (entran al fondo como vecinos) pero la caja los excluye de la detección y de la
    # estadística, como la grilla excluye lo que queda fuera de ella. detectar_mirova pone NaN en el borde de la matriz.
    rr, cc = np.nonzero(dentro)
    r0, r1 = max(rr.min() - 2, 0), min(rr.max() + 3, lat.shape[0])
    c0, c1 = max(cc.min() - 2, 0), min(cc.max() + 3, lat.shape[1])
    sl = (slice(r0, r1), slice(c0, c1))
    lat, lon, mir, tir, box = lat[sl], lon[sl], mir[sl], tir[sl], box[sl]
    if sensor_zenith is not None:
        sensor_zenith = np.asarray(sensor_zenith, float)[sl]
    mask, d = MV.detectar_mirova(mir, tir, box, dayflag, sunglint, devolver_diag=True, lam_mir=LAM,
                                 lam_tir=FAM["lam_tir"])
    v = MV.vrp_mirova(mir, mask, coef=COEF)
    vrp = v["VRP_MW"]
    if area_real and v["npix"]:
        fondo = fondo_via(mir, mask, halo=True)
        z = np.clip(np.abs(np.asarray(sensor_zenith, float)), 0, 89)
        fac = 1.0 / np.cos(np.radians(z)) ** 3
        vrp = float(np.nansum((mir[mask] - fondo[mask]) * fac[mask])) * COEF
    vla, vlo = vent_latlon
    dcen = None
    if v["npix"]:
        cu = cumulo(mask, mir)
        dcen = float(np.nanmin(MV._haversine(lat[cu], lon[cu], vla, vlo)))
    return {"npix": int(v["npix"]), "vrp_mw": (0.0 if not v["npix"] else round(float(vrp), 3)),
            "motivo": d.get("motivo"), "dist_min_cumulo_km": dcen, "n_dentro": int(dentro.sum())}


# ---------------------------------------------------------------------------------------------- todo junto
def correr_brazos(rad, lat_mxd03, lon_mxd03, lat_5km, lon_5km, grilla, vent_latlon, volcan_latlon, inner_km, sensor,
                  dayflag, sunglint, sensor_zenith, brazos=BRAZOS):
    """Un dict brazo -> resumen. dayflag y sunglint los da el llamador (los de la vía para esa pasada)."""
    out = {}
    base = preparar_grilla(rad, lat_mxd03, lon_mxd03, grilla, vent_latlon, inner_km)
    for b in brazos:
        if b in BRAZOS_GRILLA:
            m13g, m15g, box, pos = base
            rec = correr_en_grilla(b, m13g, m15g, grilla, box, dayflag, sunglint, pos, inner_km, sensor, volcan_latlon)
        elif b == "RN":
            m13g, m15g, box, pos = preparar_grilla(rad, lat_mxd03, lon_mxd03, grilla, vent_latlon, inner_km,
                                                   remuestreo=remuestrear_vecino)
            rec = correr_en_grilla("V0", m13g, m15g, grilla, box, dayflag, sunglint, pos, inner_km, sensor,
                                   volcan_latlon)
        elif b == "G5":
            m13g, m15g, box, pos = preparar_grilla(rad, lat_5km, lon_5km, grilla, vent_latlon, inner_km)
            rec = correr_en_grilla("V0", m13g, m15g, grilla, box, dayflag, sunglint, pos, inner_km, sensor,
                                   volcan_latlon)
        elif b in ("NAT", "NAT_AREA"):
            out[b] = correr_nativo(rad, lat_mxd03, lon_mxd03, grilla, vent_latlon, inner_km, dayflag, sunglint,
                                   sensor_zenith, area_real=(b == "NAT_AREA"))
            continue
        else:
            raise ValueError(b)
        out[b] = resumen(rec)
        out[b]["_record"] = rec
    return out


def resumen(rec):
    pc = rec.get("primary_cluster") or {}
    return {"npix": rec.get("n_anomalous_pixels"), "vrp_mw": rec.get("vrp_mw"), "pc_vrp_mw": pc.get("vrp_mw"),
            "distance_class": rec.get("distance_class"), "pc_dist_km": pc.get("centroid_dist_km"),
            "motivo": (rec.get("diag_codigo_mirova") or {}).get("motivo_vacio"),
            "celdas": sorted((p["fila"], p["col"]) for p in (rec.get("anomaly_pixels") or []))}
