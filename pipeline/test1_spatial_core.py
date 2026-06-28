# ════════════════════════════════════════════════════════════════════
# FICHA SDA · test1_spatial_core.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Conservar solo el foco compacto del Test 1 (no el halo difuso de 1-3 km), para que
#                 la magnitud no se infle ~8-30× vs MIROVA sobre glaciar nevado.
# Lógica        : Discriminante ESPACIAL (no termico): conserva el pixel de maxima energia (anti-FN),
#                 los pixeles a ≤ r_core_km de ese pico, y la lava extendida genuina (bt ≥ bt_ext_k).
# Modelo/método : Regla determinista (analogo pipeline del Nucleo F5' display). Funcion pura, sin I/O.
# Datos entrada : Mascara hot, VRP por pixel, lat/lon/bt (radiancia derivada). SIN datos personales.
# Variables     : r_core_km (radio del foco), bt_ext_k (umbral lava extendida).
# Limitaciones  : Asume foco compacto; una anomalia genuinamente extendida (lacolito PCC) se recorta
#                 — por eso el gate por t_bg fue refutado (A54/S86) y el discriminante es espacial.
# Refs/datos    : docs/S99_AUDIT_SYNTHESIS.md; Coppola 2015 (Test 1). Entrenamiento: No aplica.
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""S99 Candidato B — recorte de compacidad espacial para el path Test 1.

Problema (causa raíz S99, `docs/S99_AUDIT_SYNTHESIS.md`): el Test 1 integrado-ROI
(Coppola 2015) es un test de DETECCIÓN — su `mask_contributing` marca todo píxel del
ROI por encima de la mediana del fondo. Sobre el glaciar nevado de Tupungatito, en
invierno, eso es el mosaico nieve/roca entero (anillo difuso de 1-3 km). Como el VRP
suma todos esos píxeles, la magnitud se infla ~8-30× vs MIROVA, que reporta el foco
compacto (~0.2 MW estable todo el año).

El discriminante correcto, confirmado con datos (auditoría S99), es ESPACIAL — foco
compacto vs halo difuso — NO térmico (gate por t_bg refutado, A54/S86: los records
correctos de marzo tienen el mismo t_bg que los inflados de invierno).

`spatial_core_filter` conserva solo el foco compacto: el píxel de máxima energía
(SIEMPRE, guard anti-falso-negativo), los píxeles a ≤ r_core_km de ese pico, y los
píxeles de lava extendida genuina (bt ≥ bt_ext_k). Es el análogo en pipeline del
Núcleo F5' display (frontend `f5CoreMagnitude`, S95). Función pura, sin I/O.
"""
from __future__ import annotations

import numpy as np

from pipeline.scan_geometry import haversine_km


def spatial_core_filter(
    hot_mask: np.ndarray,
    vrp_per_pixel: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    bt: np.ndarray,
    r_core_km: float = 0.75,
    bt_ext_k: float = 295.0,
) -> dict:
    """Recorta `hot_mask` al foco compacto alrededor del píxel de máxima energía.

    Args:
        hot_mask: bool 2-D, píxeles candidatos (p.ej. test1_hot_filtered).
        vrp_per_pixel: float 2-D, VRP MW por píxel (0 fuera de hot_mask). Define
            el "pico de energía".
        lat, lon: float 2-D, coordenadas (deg) con la misma forma.
        bt: float 2-D, brightness temperature (K). Para preservar lava extendida.
        r_core_km: radio del núcleo alrededor del pico (km).
        bt_ext_k: BT mínima para conservar un píxel lejano como lava extendida real.

    Returns:
        dict con:
          mask (np.ndarray bool): máscara recortada.
          peak_lat, peak_lon (float | None): coordenadas del píxel pico.
          n_in (int): píxeles conservados. n_out (int): píxeles descartados.
    """
    hot_mask = np.asarray(hot_mask, dtype=bool)
    out = {"mask": hot_mask.copy(), "peak_lat": None, "peak_lon": None,
           "n_in": int(hot_mask.sum()), "n_out": 0}

    idx = np.where(hot_mask)
    if len(idx[0]) == 0:
        return out

    vrp_per_pixel = np.asarray(vrp_per_pixel, dtype=np.float64)
    # Píxel de máxima energía entre los candidatos (el "foco").
    vals = vrp_per_pixel[idx]
    k_peak = int(np.argmax(vals))
    pr, pc = int(idx[0][k_peak]), int(idx[1][k_peak])
    peak_lat = float(lat[pr, pc])
    peak_lon = float(lon[pr, pc])

    # Distancia de cada píxel candidato al pico.
    lat_c = lat[idx]
    lon_c = lon[idx]
    dist_to_peak = haversine_km(peak_lat, peak_lon, lat_c, lon_c)
    bt_c = np.asarray(bt, dtype=np.float64)[idx]

    keep = (dist_to_peak <= r_core_km) | (bt_c >= bt_ext_k)
    keep[k_peak] = True  # el pico SIEMPRE se conserva (anti-FN)

    new_mask = np.zeros_like(hot_mask)
    new_mask[idx[0][keep], idx[1][keep]] = True

    out["mask"] = new_mask
    out["peak_lat"] = peak_lat
    out["peak_lon"] = peak_lon
    out["n_in"] = int(new_mask.sum())
    out["n_out"] = int(hot_mask.sum()) - int(new_mask.sum())
    return out
