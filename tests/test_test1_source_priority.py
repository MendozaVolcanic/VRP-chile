"""Tests S111 — Parte A del fix de magnitud Muy Bajo (design 2026-06-16-test1-lowmag).

El recompute del VRP Test1 (process_viirs.py:1545-1625) está gateado por
final_hotspot_source=='test1'. Cuando un cluster cercano DÉBIL (1 píxel, vrp≈0) tapa
al Test1 en la cascada, source queda 'eruption' → la magnitud colapsa a 0 (FN de la
reactivación de NdC, 0.06 MW). El fix: cuando el Test1 detecta summit Y el cluster
rival no aporta magnitud real, el Test1 gana la fuente (helper puro, testeable sin pyhdf).
"""
from pipeline.test1_integrated import resolve_test1_source_priority

EPS = 0.01


def _call(**kw):
    base = dict(test1_summit_hit=False, eruption_far=False, only_test1_source=False,
                cluster_vrp_mw=5.0, weak_cluster_enabled=False, weak_cluster_eps=EPS)
    base.update(kw)
    return resolve_test1_source_priority(**base)


def test_regla_d_clasica_eruption_far():
    # Regla D (S30): Test1 summit + eruption far → Test1 gana (independiente del gate nuevo).
    assert _call(test1_summit_hit=True, eruption_far=True) is True


def test_only_test1_source_clasico():
    # S44: Test1 única fuente → gana.
    assert _call(only_test1_source=True) is True


def test_gate_off_no_roba_al_cluster_cercano():
    # Sin el flag, un cluster cercano débil sigue ganando (comportamiento legacy).
    assert _call(test1_summit_hit=True, eruption_far=False, cluster_vrp_mw=0.0,
                 weak_cluster_enabled=False) is False


def test_gate_on_cluster_debil_test1_gana():
    # EL FIX: Test1 summit + cluster trivialmente débil (vrp<ε) → Test1 gana → recompute.
    assert _call(test1_summit_hit=True, cluster_vrp_mw=0.0,
                 weak_cluster_enabled=True) is True
    assert _call(test1_summit_hit=True, cluster_vrp_mw=None,
                 weak_cluster_enabled=True) is True


def test_gate_on_cluster_fuerte_no_se_toca():
    # Guard: si el cluster aporta magnitud real (>=ε), NO se lo roba el Test1.
    assert _call(test1_summit_hit=True, cluster_vrp_mw=5.0,
                 weak_cluster_enabled=True) is False


def test_gate_on_sin_test1_summit_no_aplica():
    # El fix requiere que el Test1 haya detectado summit; si no, no aplica.
    assert _call(test1_summit_hit=False, cluster_vrp_mw=0.0,
                 weak_cluster_enabled=True) is False


def test_retorno_es_bool_python():
    import numpy as np
    r = resolve_test1_source_priority(test1_summit_hit=True, eruption_far=False,
                          only_test1_source=False, cluster_vrp_mw=np.float64(0.0),
                          weak_cluster_enabled=True, weak_cluster_eps=EPS)
    assert r is True and isinstance(r, bool)
