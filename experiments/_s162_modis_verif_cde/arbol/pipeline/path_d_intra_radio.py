# ════════════════════════════════════════════════════════════════════
# FICHA SDA · path_d_intra_radio.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Evitar que el path D (dNTI contextual) clasifique como deteccion ruido lejano al
#                 crater (89% de FPs MODIS a >10 km), que MIROVA tagea RUTINA(vrp=0).
# Lógica        : Restringe SOLO los pixeles del path D al inner_radius_km del KMZ MIROVA. Paths A
#                 (BT clasico) y B (NTI absoluto) NO se tocan — una erupcion real lejana pasa por A/B.
# Modelo/método : Regla determinista (gate geometrico por inner_radius). Funcion pura, sin I/O.
# Datos entrada : Mascara dNTI contextual + distancia al vent por pixel. SIN datos personales.
# Variables     : inner_radius_km (oficial KMZ MIROVA por volcan), flag enable_path_d_intra_radio_gate.
# Limitaciones  : Drift documentado vs Coppola 2016a (el paper no exige restriccion espacial al path D);
#                 justificado empiricamente (las 1332 ALERTA MIROVA Tier A caen 100% dentro del inner).
# Refs/datos    : docs/F_S81_A_FASE1_DIAGNOSIS.md; KMZ MIROVA (volcanoes.yaml). No aplica ML.
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""S83 F-S81-A Fase 2 — Gate Path D MODIS intra-radio per-volcán.

Motivación: 99.5% de FPs MODIS Tier A son Path D (dNTI contextual 8-vecinos)
puro disparando lejos del cráter (89% a >10 km, 53% a >20 km). MIROVA tagged
RUTINA(vrp=0.0) en 98% de esos casos → gate intra-ROI no replicado en VRP
Chile. Detalle: docs/F_S81_A_FASE1_DIAGNOSIS.md.

Sanity check Fase 1b (docs/F_S81_A_FASE1B_SANITY_P95.md) mostró que el método
"p95 empírico ALERTA_TERMICA MODIS" colapsa al fallback inner_radius_km en
10/11 Tier A (solo Lascar tiene N>=10 ALERTAs, p95=2km < inner=5km). Por eso
la versión A-simplificada usa directamente inner_radius_km del KMZ MIROVA
oficial ya cargado en volcanoes.yaml — sin script offline ni nuevo campo
per-volcán.

El gate solo restringe Path D (dnti_ctx_hot). Paths A (BT clásico) y B
(NTI absoluto) siguen disparando sin restricción — erupciones reales
grandes con flujo lejos del cráter pasan por A o B, no requieren D.
"""
from __future__ import annotations

import numpy as np


def apply_intra_radio_gate(
    *,
    dnti_ctx_hot: np.ndarray,
    vent_dist_per_pixel: np.ndarray,
    inner_radius_km: float | None,
    enabled: bool,
) -> np.ndarray:
    """Mascarea pixels Path D fuera del inner_radius_km del vent.

    Args:
        dnti_ctx_hot: máscara booleana 2D de hits Path D dNTI contextual.
        vent_dist_per_pixel: distancia per-píxel al vent (km), misma shape.
        inner_radius_km: radio del cono volcánico per-volcán (KMZ MIROVA).
            Si None, fallback no-op (vols sin entrada en volcanoes.yaml).
        enabled: si False, devuelve la máscara intacta (passthrough).

    Returns:
        Máscara booleana 2D filtrada. Pixels con dist > inner_radius_km
        quedan en False cuando el gate está activo.
    """
    if not enabled:
        return dnti_ctx_hot
    if inner_radius_km is None:
        return dnti_ctx_hot
    intra_radius = vent_dist_per_pixel <= inner_radius_km
    return dnti_ctx_hot & intra_radius
