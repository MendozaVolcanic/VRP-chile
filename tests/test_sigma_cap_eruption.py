"""Tests del sigma-cap en eruption-path (P3 Tema F S15).

Paridad con MODIS: MAX_SIGMA_COMPONENT_K limita la inflacion del
threshold por sigma_bg heterogeneo (Tupungatito glaciar, Villarrica
cono glaciar).

Antes del fix: threshold = max(5, 3*sigma_bg). Con sigma_bg=3K,
threshold = 9K. Pixels reales a DeltaT=8K rechazados.

Despues: threshold = max(5, min(3*sigma_bg, 7)). Con sigma_bg=3K,
threshold = 7K. Pixels a DeltaT=8K pasan.
"""
import os
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import importlib
import pipeline.profile
importlib.reload(pipeline.profile)


def test_max_sigma_component_k_set_to_7():
    """Confirmar constante cargada desde profile."""
    from pipeline.profile import MAX_SIGMA_COMPONENT_K
    assert MAX_SIGMA_COMPONENT_K == 7.0


def test_sigma_cap_formula():
    """Demostrar que el cap evita la inflacion.

    Sin cap: threshold_sin = max(5, 3*sigma).
    Con cap: threshold_con = max(5, min(3*sigma, 7)).

    Para sigma=2: ambos = max(5, 6) = 6. Sin diferencia (sigma chico).
    Para sigma=3: sin = 9, con = 7. Con salva 2K.
    Para sigma=4: sin = 12, con = 7. Con salva 5K.
    """
    ANOMALY = 5.0
    NSIGMA = 3.0
    CAP = 7.0

    # Sigma bajo: sin diferencia
    sigma = 1.5
    assert max(ANOMALY, NSIGMA * sigma) == max(ANOMALY, min(NSIGMA * sigma, CAP))

    # Sigma medio: el cap empieza a actuar
    sigma = 3.0
    sin_cap = max(ANOMALY, NSIGMA * sigma)   # 9
    con_cap = max(ANOMALY, min(NSIGMA * sigma, CAP))   # 7
    assert sin_cap > con_cap
    assert con_cap == 7.0

    # Sigma alto (Tupungatito glaciar escenario): cap crucial
    sigma = 5.0
    sin_cap = max(ANOMALY, NSIGMA * sigma)   # 15
    con_cap = max(ANOMALY, min(NSIGMA * sigma, CAP))   # 7
    assert sin_cap - con_cap == 8.0
    assert con_cap == 7.0
