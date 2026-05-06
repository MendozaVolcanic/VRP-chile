"""S33 R1+R7 — TDD para mirova_eq_vrp + casos sintéticos del bug S33.

Estos tests previenen recurrencia del bug S33: 'distance_class=summit pero
primary_cluster lejos en Salar daba pc.vrp_mw del Salar como VRP del cráter'.

Cada test es un caso fronterizo identificado durante la auditoría S33.
"""
from __future__ import annotations

from pipeline.audit_metrics import (
    mirova_eq_vrp,
    INNER_RADIUS_KM_TIER_A,
    DEFAULT_INNER_KM,
)


# === R1: tests directos del bug S33 ===

def test_bug_s33_summit_class_pero_cluster_far_devuelve_cero():
    """Bug S33 reproducido en test: Lascar 2026-02-14 MODIS_TERRA case.

    distance_class='summit' (Test 1 final_hotspot cerca del vent)
    PERO primary_cluster a 24 km (Salar Atacama).
    Lascar inner_radius_km=5. → DEBE devolver 0.

    Antes del fix devolvía 19389 MW.
    """
    rec = {
        'distance_class': 'summit',
        'vrp_mw': 0,
        'primary_cluster': {
            'centroid_dist_km': 24.17,
            'vrp_mw': 19389.8,
            'n_pixels': 5,
        },
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 0


def test_pc_dentro_inner_radius_devuelve_pc_vrp():
    """Caso normal: pc cerca del cráter → return pc.vrp_mw."""
    rec = {
        'distance_class': 'summit',
        'vrp_mw': 100,
        'primary_cluster': {
            'centroid_dist_km': 0.5,
            'vrp_mw': 2.5,
            'n_pixels': 26,
        },
    }
    assert mirova_eq_vrp(rec, volcano_name='Lastarria') == 2.5


def test_distance_class_far_devuelve_cero():
    """Pipeline ya marcó como far → MIROVA tampoco reportaría."""
    rec = {
        'distance_class': 'far',
        'vrp_mw': 250.0,
        'primary_cluster': {
            'centroid_dist_km': 22.0,
            'vrp_mw': 100.0,
        },
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 0


def test_legacy_record_sin_primary_cluster_fallback_a_vrp_mw():
    """Records pre-S27 sin cluster → fallback a vrp_mw global."""
    rec = {
        'distance_class': 'summit',
        'vrp_mw': 5.0,
        # no primary_cluster
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 5.0


def test_pc_sin_centroid_dist_devuelve_pc_vrp():
    """Records sin centroid_dist_km en pc → no se valida, return pc.vrp_mw."""
    rec = {
        'distance_class': 'summit',
        'vrp_mw': 3.0,
        'primary_cluster': {
            'vrp_mw': 1.5,
            # no centroid_dist_km
        },
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 1.5


def test_record_none_devuelve_cero():
    """Robustez."""
    assert mirova_eq_vrp(None) == 0


def test_inner_km_explicit_overrides_volcano_lookup():
    """Override innerKm por argumento."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 8.0, 'vrp_mw': 5.0},
    }
    # Lascar inner=5, pc=8 → 0
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 0
    # Override inner_km=10 → pasa
    assert mirova_eq_vrp(rec, inner_km=10) == 5.0


def test_unknown_volcano_usa_default_inner():
    """Volcán fuera de Tier A → DEFAULT_INNER_KM=10."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 8.0, 'vrp_mw': 5.0},
    }
    # Volcán desconocido + pc_dist=8 < default 10 → pasa
    assert mirova_eq_vrp(rec, volcano_name='UnknownVolcano') == 5.0
    # Volcán desconocido + pc_dist=15 > default 10 → 0
    rec['primary_cluster']['centroid_dist_km'] = 15
    assert mirova_eq_vrp(rec, volcano_name='UnknownVolcano') == 0


# === R7 cases sintéticos: casos edge específicos del audit ===

def test_pcc_inner_20_permite_lacolito_8km():
    """PCC tiene inner=20 (lacolito offset). Cluster a 8km debe pasar."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 8.5, 'vrp_mw': 12.0},
    }
    assert mirova_eq_vrp(rec, volcano_name='PuyehueCordonCaulle') == 12.0


def test_pcc_inner_20_descarta_cluster_a_22km():
    """PCC inner=20: cluster a 22km debe descartarse."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 22.0, 'vrp_mw': 50.0},
    }
    assert mirova_eq_vrp(rec, volcano_name='PuyehueCordonCaulle') == 0


def test_planchon_inner_3_descarta_cluster_a_4km():
    """Planchón inner=3 (estrecho). Cluster a 4km debe descartarse."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 4.0, 'vrp_mw': 5.0},
    }
    assert mirova_eq_vrp(rec, volcano_name='PlanchonPeteroa') == 0


def test_pc_vrp_zero_devuelve_cero():
    """Record con cluster pero VRP cluster = 0 → 0."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 0.5, 'vrp_mw': 0},
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 0


def test_pc_vrp_none_devuelve_cero():
    """Robustez: pc sin vrp_mw → 0."""
    rec = {
        'distance_class': 'summit',
        'primary_cluster': {'centroid_dist_km': 0.5},  # no vrp_mw
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 0


def test_inner_radius_table_completo_para_tier_a():
    """Validar que TODOS los 11 Tier A tienen inner_radius_km definido."""
    expected_tier_a = {
        'Lascar', 'Lastarria', 'Tupungatito', 'Villarrica',
        'PuyehueCordonCaulle', 'Copahue', 'NevadosDeChillan',
        'Llaima', 'Chaiten', 'PlanchonPeteroa', 'Isluga'
    }
    assert set(INNER_RADIUS_KM_TIER_A.keys()) == expected_tier_a


def test_inner_radius_values_consistent_con_kmz_oficiales():
    """Valores oficiales MIROVA KMZ documentados en CLAUDE.md."""
    assert INNER_RADIUS_KM_TIER_A['Lastarria'] == 3
    assert INNER_RADIUS_KM_TIER_A['PlanchonPeteroa'] == 3
    assert INNER_RADIUS_KM_TIER_A['Copahue'] == 4
    assert INNER_RADIUS_KM_TIER_A['Tupungatito'] == 7
    assert INNER_RADIUS_KM_TIER_A['PuyehueCordonCaulle'] == 20  # lacolito


def test_default_inner_km_conservative():
    """Default 10km es conservador (entre 7 Tupungatito y 20 PCC)."""
    assert DEFAULT_INNER_KM == 10


def test_distance_class_none_pasa_si_pc_dentro_inner():
    """Records sin distance_class explícito → permitir si pc cerca."""
    rec = {
        # no distance_class
        'primary_cluster': {'centroid_dist_km': 1.0, 'vrp_mw': 2.0},
    }
    assert mirova_eq_vrp(rec, volcano_name='Lascar') == 2.0
