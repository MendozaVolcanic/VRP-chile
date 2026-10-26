# -*- coding: utf-8 -*-
"""
FICHA SDA · Magnitud "núcleo" F5' — módulo de cálculo
Sistema      : VRP Chile (Sistema de Decisiones Automatizadas, Res. CPLT N°372)
Función      : recalcular la magnitud VRP publicada restringida al cúmulo del cráter
Datos entrada: `anomaly_pixels` y `primary_cluster` de un record ya detectado
Datos salida : magnitud en MW, o None cuando no corresponde recalcular
Alcance      : VIIRS I-band 375 m únicamente (calibración S95)
Sin datos personales. No decide la alerta: reporta magnitud de una anomalía ya detectada.

POR QUÉ EXISTE ESTE MÓDULO (S132, decisión #3 de AUDIT_S131 §4)
--------------------------------------------------------------
MIROVA no informa "toda la energía caliente de la escena": informa la del CÚMULO asociado
al cráter. Nuestro `primary_cluster.vrp_mw` agrega de más en los volcanes con halo
glaciar, porque el anillo de nieve alrededor de la cumbre aporta píxeles apenas por
encima del fondo que, sumados, pesan tanto como el foco. F5' reproduce el recorte de
MIROVA: ancla en el píxel de máxima energía del cúmulo validado y suma su vecindad
inmediata (0,75 km) más los píxeles francamente tibios (BT ≥ 295 K, que son la cola
térmica real del cuerpo caliente y no ruido de nieve).

Medido en S131 sobre 1.609 pares por pasada: F5' da 0,68 contra MIROVA donde
`pc.vrp_mw` da 0,58. Es el número MÁS cercano a la referencia, y es el que el dashboard
ya venía mostrando.

El algoritmo vivía SÓLO en JavaScript (`frontend/index.html` `f5CoreMagnitude`), se
recalculaba en cada carga de página y no quedaba escrito en ningún JSON: la cifra
publicada no era la cifra auditada. Este módulo lo trae al pipeline para poder
persistirlo. Es un PORT LITERAL — no cambia ningún número; la equivalencia con el JS se
verifica sobre los records reales del repo en
`tests/test_f5_core_python_s132.py::test_paridad_con_el_javascript`.

POR QUÉ SÓLO VIIRS375. La calibración (docs/F5_CALIBRATION_S95.md) se hizo sobre I-band.
En MODIS (1 km) y VIIRS M-band (750 m) el píxel grueso hace que el ancla "máxima energía"
salte a fuentes ajenas: el caso PCC MODIS 2026-05-30 02:55 tenía el pico a 12,82 km e
inflaba 8 → 22 MW. Ahí se conserva el cúmulo.
"""
import math

# Radio del núcleo alrededor del píxel pico. 0,75 km ≈ dos píxeles I-band (375 m).
F5_R_CORE_KM = 0.75
# Piso de BT para conservar un píxel lejano: por encima de 295 K ya no es nieve.
F5_BT_EXT_K = 295.0


def _hav_km(lat1, lon1, lat2, lon2):
    """Haversine, réplica exacta de `_havKm` del frontend (R = 6371,0 km)."""
    R, rad = 6371.0, math.pi / 180.0
    p1, p2 = lat1 * rad, lat2 * rad
    dp, dl = (lat2 - lat1) * rad, (lon2 - lon1) * rad
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def es_viirs_iband(sensor):
    """Convención del repo (A48): VIIRS_{SNPP,NOAA20,NOAA21} = I-band 375 m;
    el sufijo `_750` marca M-band. NO usar regex sobre "375"."""
    s = str(sensor or "").upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def f5_core_vrp_mw(record, inner_km):
    """Magnitud del núcleo, en MW, o None si no corresponde recalcular.

    Devuelve None (y el llamador se queda con `pc.vrp_mw`) en los tres casos donde el
    recálculo no sería confiable: sin `anomaly_pixels`, sin centroide de cúmulo validado
    donde anclar, o cuando ningún píxel guardado cae dentro de `inner_km` del centroide
    — esta última es la asimetría de schema A46/A07, en la que el cúmulo agrega energía
    real pero los píxeles persistidos están todos lejos (caso PP 2026-05-30: cúmulo de
    19 px en la cumbre, `anomaly_pixels` = 3 px, uno de ellos un incendio a 19 km).
    """
    pixels = (record or {}).get("anomaly_pixels")
    if not pixels:
        return None

    pc = record.get("primary_cluster")
    if not pc or pc.get("centroid_lat") is None or pc.get("centroid_lon") is None:
        return None
    c_lat, c_lon = pc["centroid_lat"], pc["centroid_lon"]

    # Sólo el entorno del cúmulo validado: un ancla ciega puede irse a una fuente lejana
    # de mayor energía. La distancia se mide desde lat/lon del píxel, NUNCA desde
    # `dist_km`, cuyo ancla es el centro del volcán y no el cúmulo (A48).
    cand = [p for p in pixels
            if p.get("lat") is not None and p.get("lon") is not None
            and _hav_km(p["lat"], p["lon"], c_lat, c_lon) <= inner_km]
    if not cand:
        return None

    peak = 0
    for i in range(1, len(cand)):
        if (cand[i].get("vrp_mw") or 0) > (cand[peak].get("vrp_mw") or 0):
            peak = i
    p_lat, p_lon = cand[peak].get("lat"), cand[peak].get("lon")
    if p_lat is None or p_lon is None:
        return None

    total = 0.0
    for i, p in enumerate(cand):
        keep = (i == peak
                or _hav_km(p["lat"], p["lon"], p_lat, p_lon) <= F5_R_CORE_KM
                or (p.get("bt_k") or 0) >= F5_BT_EXT_K)
        if keep:
            total += (p.get("vrp_mw") or 0)
    return total
