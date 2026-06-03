"""S99 Candidato C — filtro contextual del path Test 1 (la vía más fiel a MIROVA).

El Test 1 integrado marca todo píxel sobre la mediana del anillo regional (1-3 km),
que sobre glaciar está sesgada fría → marca el halo nival entero. MIROVA marca por
criterio CONTEXTUAL (Tests 2/3, Coppola 2016a SP426.5): anómalo = supera a sus 8
vecinos inmediatos. La roca tibia rodeada de roca tibia NO es contextualmente anómala.
Este filtro intersecta los píxeles del Test 1 con la máscara contextual dNTI ya
computada (`dnti_ctx_hot`) → el VRP suma solo lo anómalo vs vecinos = comportamiento
MIROVA. Función pura, sin I/O.

Caveat (medido en A/B, no oculto): un cráter EMBEBIDO en roca tibia puede no ser
contextualmente anómalo → se cae → FN. La forma PURA (sin keep-peak) existe para que
el canario revele ese trade-off honestamente.
"""
from __future__ import annotations

import numpy as np


def apply_contextual_test1_filter(test1_mask: np.ndarray,
                                  dnti_ctx_mask) -> np.ndarray:
    """Intersecta la máscara Test 1 con la máscara contextual dNTI.

    Args:
        test1_mask: bool 2-D, píxeles del Test 1 (test1_hot_filtered).
        dnti_ctx_mask: bool 2-D de píxeles contextualmente anómalos (dnti_ctx_hot),
            o None si no disponible (paths sin dNTI contextual).

    Returns:
        bool 2-D = test1_mask ∩ dnti_ctx_mask. Si dnti_ctx_mask es None → passthrough
        (devuelve test1_mask sin cambios; el caller decide).
    """
    test1_mask = np.asarray(test1_mask, dtype=bool)
    if dnti_ctx_mask is None:
        return test1_mask
    dnti_ctx_mask = np.asarray(dnti_ctx_mask, dtype=bool)
    if dnti_ctx_mask.shape != test1_mask.shape:
        return test1_mask  # defensa: formas incompatibles → no filtrar
    return test1_mask & dnti_ctx_mask
