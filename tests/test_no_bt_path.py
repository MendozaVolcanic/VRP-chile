"""Tests S40 — cleanup paths viejos (bt_path_hot opcional).

Análisis empírico S39: bt_path_hot solo contribuye exclusivamente en
0-6 records sobre 1846 TPs operacional 30d. test1_hot y dnti_ctx_hot
son los paths dominantes.

S40: agregar flag ENABLE_BT_PATH_HOT (default True backward-compat).
Cuando OFF, bt_path_hot = zeros → solo test1 + dnti_ctx + (eti si activo)
+ nti_path dispararan.
"""
import importlib
import yaml
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_off_in_mirova_equivalent_s40(monkeypatch):
    """S40 ADOPTADO: ENABLE_BT_PATH_HOT=False en operacional.

    A/B run 25804811234 (11/11 success) confirmó retirar bt_path SUBE
    recall +1.7pp (90.5%→92.2%) sin regresión en ningún vol. Isluga +2 TP
    por menos contaminación lejana en anomaly_pixels.
    """
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_BT_PATH_HOT is False


def test_off_in_no_bt_path_profile(monkeypatch):
    """Profile A/B _no_bt_path tiene flag OFF."""
    monkeypatch.setenv("VRP_PROFILE", "_no_bt_path")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_BT_PATH_HOT is False
    # Resto del operacional adoptado debe seguir igual
    assert profile.ENABLE_VENT_ANCHORED_CLUSTERING is True
    assert profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER is True
    assert profile.ENABLE_TEST1_LBG_GLOBAL is True


def test_no_bt_path_profile_yaml_loads():
    p = REPO / 'pipeline' / 'profiles' / '_no_bt_path.yaml'
    assert p.exists()
    with open(p, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    paths = cfg['paths']
    assert paths['enable_bt_path_hot'] is False
    assert paths['enable_vent_anchored_clustering'] is True
    assert paths['enable_pixel_level_distance_filter'] is True
    assert paths['enable_test1_lbg_global'] is True
    assert cfg['output']['data_subdir'] == '_no_bt_path'


def test_bt_path_on_profile_loads():
    """S72 F2.6.e A/B — profile mirova_equivalent_bt_path_on_v1 (revertir S40).

    Profile revierte S40 reactivando bt_path_hot para testar hipótesis F2.6.c
    rank 1 (la reducción Lascar S26→S71 388→0.966 MW es atribuible al cleanup
    S40 que retiró 1453 pixels BT del Salar de Atacama / ROI lejana).

    Verifica:
      - YAML carga.
      - enable_bt_path_hot: true (override clave revertir S40).
      - resto de la deriva S38-S61 intacta (vent_anchored, pixel_level_filter,
        test1_lbg_global, local_kernel_bg, cap Opción C, drift234 first+second).
      - data_subdir aislado (no contamina operacional).
    """
    p = REPO / 'pipeline' / 'profiles' / 'mirova_equivalent_bt_path_on_v1.yaml'
    assert p.exists()
    with open(p, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    paths = cfg['paths']
    # Override clave A/B F2.6.e
    assert paths['enable_bt_path_hot'] is True
    # Deriva S38-S61 intacta — todo igual al operacional excepto bt_path
    assert paths['enable_vent_anchored_clustering'] is True
    assert paths['enable_pixel_level_distance_filter'] is True
    assert paths['enable_test1_lbg_global'] is True
    assert paths['enable_local_kernel_bg'] is True
    assert paths['enable_first_pass_tests_2_and_3'] is True
    assert paths['enable_second_pass_adjacent'] is True
    # Cap Opción C S71 intacto (operacional actual)
    assert paths['path_d_only_cap_mw'] == 5.0
    assert paths['path_d_only_cap_tbg_max_k'] == 270.0
    # Aislamiento dashboard / operacional
    assert cfg['profile'] == 'mirova_equivalent_bt_path_on_v1'
    assert cfg['output']['data_subdir'] == 'mirova_equivalent_bt_path_on_v1'
