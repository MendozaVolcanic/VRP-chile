"""Tests S39 D4 per-volcano — lbg_global_compatible field gating.

Combo C.1 S38 (run 25762044191) mostró que D4 fix (L_bg global) NO es
universal: ayuda en volcanes con cráter caliente permanente (Lascar
fumarola crónica, Lastarria sulfataras) pero EMPEORA en glaciares
(Tupungatito -1 TP, Planchón -1 TP).

S39 fix: combinar profile flag ENABLE_TEST1_LBG_GLOBAL con field per-volcán
`lbg_global_compatible` en volcanoes.yaml. Solo aplica cuando AMBOS son
true. Default per-vol = false (safe).

Estos tests verifican:
1. volcanoes.yaml tiene lbg_global_compatible=true SOLO en Lascar + Lastarria
2. signature de process_*.calculate_vrp acepta lbg_global_compatible kwarg
3. run_pipeline.py pasa el field desde volcano dict
"""
import yaml
from pathlib import Path
import inspect

from pipeline import process_modis, process_viirs, process_viirs_mod

REPO = Path(__file__).resolve().parent.parent


def test_lbg_global_compatible_in_volcanoes_yaml():
    """Confirma que SOLO Lascar y Lastarria tienen lbg_global_compatible=true."""
    p = REPO / 'volcanoes.yaml'
    with open(p, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    volcanoes = cfg['volcanoes']

    enabled = [v['name'] for v in volcanoes
               if v.get('lbg_global_compatible') is True]
    assert 'Lascar' in enabled, 'Lascar debe tener lbg_global_compatible=true (cráter caliente permanente)'
    assert 'Lastarria' in enabled, 'Lastarria debe tener lbg_global_compatible=true (fumarolas crónicas)'
    # Tupungatito y Planchón explicitamente NO deben tener el flag (glaciares)
    excluded = ['Tupungatito', 'PlanchonPeteroa']
    for vname in excluded:
        assert vname not in enabled, (
            f'{vname} NO debe tener lbg_global_compatible=true — glaciar frío '
            'donde D4 fix regresiona (combo C.1 S38 -1 TP)'
        )


def test_process_modis_accepts_lbg_global_compatible_kwarg():
    """process_modis.calculate_vrp tiene el kwarg con default False."""
    sig = inspect.signature(process_modis.calculate_vrp)
    assert 'lbg_global_compatible' in sig.parameters
    p = sig.parameters['lbg_global_compatible']
    assert p.default is False, 'Default debe ser False (safe)'


def test_process_viirs_accepts_lbg_global_compatible_kwarg():
    sig = inspect.signature(process_viirs.calculate_vrp)
    assert 'lbg_global_compatible' in sig.parameters
    assert sig.parameters['lbg_global_compatible'].default is False


def test_process_viirs_mod_accepts_lbg_global_compatible_kwarg():
    sig = inspect.signature(process_viirs_mod.calculate_vrp)
    assert 'lbg_global_compatible' in sig.parameters
    assert sig.parameters['lbg_global_compatible'].default is False


def test_run_pipeline_passes_lbg_global_compatible():
    """run_pipeline.py debe pasar `volcano.get('lbg_global_compatible', False)`
    a las 3 invocaciones de calculate_vrp.
    """
    p = REPO / 'scripts' / 'run_pipeline.py'
    src = p.read_text(encoding='utf-8')
    # Esperamos 3 ocurrencias (una por procesador)
    n = src.count("lbg_global_compatible=volcano.get(\"lbg_global_compatible\", False)")
    assert n == 3, f'Esperaba 3 invocaciones con lbg_global_compatible, encontré {n}'


def test_d4_per_volcano_profile_exists_and_loads():
    """Perfil _d8_d4_per_vol.yaml combo activa ambos flags y será el A/B target."""
    p = REPO / 'pipeline' / 'profiles' / '_d8_d4_per_vol.yaml'
    assert p.exists(), f'{p} missing — creará el A/B target'
    with open(p, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    paths_cfg = cfg['paths']
    # Combo combina vent_anchored (S38 adoptado) + D4 per-vol
    assert paths_cfg['enable_vent_anchored_clustering'] is True
    assert paths_cfg['enable_pixel_level_distance_filter'] is True
    assert paths_cfg['enable_test1_lbg_global'] is True  # profile flag ON
    # data_subdir aislado
    assert cfg['output']['data_subdir'] == '_d8_d4_per_vol'
