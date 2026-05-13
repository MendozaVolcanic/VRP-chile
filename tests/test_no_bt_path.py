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
