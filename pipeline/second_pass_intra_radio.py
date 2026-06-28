# ════════════════════════════════════════════════════════════════════
# FICHA SDA · second_pass_intra_radio.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Evitar que el segundo pase (recaptura de vecinos) rescate ruido distribuido lejos
#                 del cono en cirrus/glaciar parcialmente calido (NdC=1247 recapturas, PP=776).
# Lógica        : Aplica el gate intra-radio SOLO a los pixeles NUEVOS del second pass; los del primer
#                 pase NO se tocan (ya pasaron sus propios filtros). Mismo principio que path_d_intra_radio.
# Modelo/método : Regla determinista (gate geometrico por inner_radius). Funcion pura, sin I/O.
# Datos entrada : Mascara newly_active del second pass + distancia al vent. SIN datos personales.
# Variables     : inner_radius_km (KMZ MIROVA), flag enable_second_pass_intra_radio_gate (default OFF).
# Limitaciones  : Drift vs Coppola 2016a §347-356 (el paper no exige restriccion espacial al second
#                 pass); justificacion empirica identica a F-S81-A (1332 ALERTA Tier A dentro del inner).
# Refs/datos    : docs/R3_RESIDUAL_BY_PATH.md; KMZ MIROVA. Entrenamiento: No aplica (sin ML).
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""S85 Fase B' — Gate intra-radio sobre pixels NUEVOS del second_pass_recapture.

Motivación: audit B0 (docs/R3_RESIDUAL_BY_PATH.md) mostró que 87.7% de los
106 R3 violators del operacional post-S84 NO tienen ningún path del primer
pase activo. Los volcanes con más R3 (NdC=24, Llaima=18, Copahue=14, PP=11)
son justamente los que tienen `n_second_pass_recapture` masivo (NdC=1247,
PP=776, Copahue=648). El segundo pase de `second_pass_adjacent`
(`pipeline/detection_context.py`) no tiene restricción espacial — recaptura
cualquier pixel de la escena que cumpla Tests 2∧3 con la media 8-vecinos
recomputada (excluyendo activos del primer pase). En cirrus uniforme o
glaciar parcialmente cálido, esto rescata ruido distribuido lejos del cono.

Sanity empírico: las 1332 ALERTAs MIROVA Tier A (CSV + OCR, S84) caen 100%
dentro del inner_radius_km del KMZ MIROVA. Cero excepciones. Por tanto,
cualquier pixel recapturado por el segundo pase fuera del inner_radius es
con muy alta probabilidad ruido, no actividad volcánica real.

Diseño:
- Gate aplicado SOLO a pixels nuevos del second pass (newly_active).
- Pixels del first pass (hot_mask_2d) NO se tocan — ya pasaron sus
  propios filtros.
- Flag toggleable: `enable_second_pass_intra_radio_gate` (default False
  hasta validación A/B + adopción).

Drift documentado vs paper Coppola 2016a SP 426.5 §347-356: el paper no
exige restricción espacial al second pass. Justificación empírica del
drift: idéntica a la de F-S81-A (adoptada S84, mismo principio intra-radio).
"""
from __future__ import annotations

import numpy as np


def apply_second_pass_intra_radio_gate(
    *,
    first_pass_mask: np.ndarray,
    final_active_mask: np.ndarray,
    vent_dist_per_pixel: np.ndarray,
    inner_radius_km: float | None,
    enabled: bool,
) -> np.ndarray:
    """Mascarea pixels NUEVOS del second pass que caen fuera del inner_radius_km.

    Args:
        first_pass_mask: máscara booleana 2D de pixels marcados por el
            primer pase (pre-second_pass_adjacent). NO se modifica.
        final_active_mask: máscara booleana 2D devuelta por
            second_pass_adjacent (first_pass_mask | newly_recaptured).
            Misma shape que first_pass_mask.
        vent_dist_per_pixel: distancia per-píxel al vent en km, misma shape.
        inner_radius_km: radio del cono per-volcán (KMZ MIROVA). Si None,
            fallback no-op (volcán sin entrada en volcanoes.yaml).
        enabled: si False, devuelve final_active_mask intacto (passthrough).

    Returns:
        Máscara booleana 2D filtrada:
        - Pixels del first pass: preservados sin cambio.
        - Pixels nuevos del second pass dentro de inner_radius_km: preservados.
        - Pixels nuevos del second pass fuera de inner_radius_km: descartados.

    El conteo `n_second_pass_recapture` que el caller persiste como
    `diag_n_second_pass_recapture` debe recalcularse sobre la máscara
    devuelta (no la original) para reflejar el efecto del gate.
    """
    if not enabled:
        return final_active_mask
    if inner_radius_km is None:
        return final_active_mask
    newly_active = final_active_mask & ~first_pass_mask
    intra_radius = vent_dist_per_pixel <= inner_radius_km
    newly_active_gated = newly_active & intra_radius
    return first_pass_mask | newly_active_gated
