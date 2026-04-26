"""Schema-source test: marca explícitamente la divergencia local ROI threshold
entre process_modis y process_viirs. Documentado como D7 en docs/DRIFTS_S17.md.

Detección: audit S22 mostró que process_modis.py:285-288 aplica un filtro local:
    local_threshold = roi_p95 + max(3.0, 2.0 * roi_std)
    effective_threshold = max(t_bg + threshold, local_threshold)
mientras que process_viirs.py y process_viirs_mod.py NO lo hacen.

Implicancia: para mismo evento físico, MODIS y VIIRS pueden detectar conjuntos
distintos de pixels — MODIS rechaza pixels que solo son levemente más calientes
que el percentile 95 del ROI, VIIRS no.

Estos tests NO fallan en estado actual — solo alertan si el código diverge sin
actualizar D7 en DRIFTS_S17.md.
"""
from pathlib import Path

PIPELINE = Path(__file__).parent.parent / "pipeline"


def test_modis_has_local_roi_threshold_documented():
    """Sanity: process_modis.py tiene la fórmula local ROI threshold."""
    src = (PIPELINE / "process_modis.py").read_text(encoding="utf-8")
    has_formula = "roi_p95" in src and "roi_std" in src and "local_threshold" in src
    assert has_formula, (
        "process_modis.py debería tener la fórmula local ROI threshold "
        "(roi_p95 + max(3.0, 2.0*roi_std)). Si fue eliminada, actualizar D7 "
        "en docs/DRIFTS_S17.md y este test."
    )


def test_viirs_375m_known_to_lack_local_roi_threshold():
    """D7 documentado: process_viirs (375m I-band) NO tiene la fórmula.
    Si se agrega, actualizar D7 en DRIFTS_S17.md y este test."""
    src = (PIPELINE / "process_viirs.py").read_text(encoding="utf-8")
    has_formula = (
        "roi_p95 + max(3.0, 2.0" in src
        or "roi_p95 + max(3," in src
        or "local_threshold = roi_p95" in src
    )
    assert not has_formula, (
        "process_viirs.py AHORA tiene la fórmula local ROI threshold que "
        "antes solo estaba en MODIS. Si fue agregada deliberadamente, "
        "actualizar D7 en docs/DRIFTS_S17.md y este test."
    )


def test_viirs_750m_has_local_roi_threshold_like_modis():
    """process_viirs_mod.py (M-band 750m) SÍ tiene local ROI threshold,
    igual que MODIS. Solo VIIRS 375m carece de este filtro (D7).
    """
    src = (PIPELINE / "process_viirs_mod.py").read_text(encoding="utf-8")
    has_formula = "local_threshold = roi_p95" in src and "max(t_bg + threshold, local_threshold)" in src
    assert has_formula, (
        "process_viirs_mod.py debería tener local ROI threshold (parity MODIS). "
        "Si fue eliminado, actualizar D7 en docs/DRIFTS_S17.md y este test."
    )


def test_d7_documented_in_drifts():
    """D7 debe estar mencionado en docs/DRIFTS_S17.md."""
    drifts_md = (PIPELINE.parent / "docs" / "DRIFTS_S17.md").read_text(encoding="utf-8")
    assert "D7" in drifts_md, (
        "D7 (local ROI threshold MODIS-only) debe estar documentado en "
        "docs/DRIFTS_S17.md."
    )
    assert "Local ROI threshold" in drifts_md or "local ROI threshold" in drifts_md, (
        "D7 sección debe mencionar 'local ROI threshold' explícitamente."
    )
