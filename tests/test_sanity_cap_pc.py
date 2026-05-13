"""Tests S41 — sanity cap a primary_cluster.vrp_mw.

Caso real: Lastarria 2026-04-23 01:50 MODIS_TERRA granule sensor saturado
(BT=566K en 382 pixels) produjo pc.vrp_mw=1,639,629 MW. El sanity cap S19
M4 (50,000 MW) original aplicaba solo a record.vrp_mw (sum total) que
estaba en 0 post-floor, dejando pasar el garbage en pc.vrp_mw que el
dashboard sí lee via mirovaEqVrp.

S41 fix: agregar cap también a primary_cluster.vrp_mw.
"""
import pytest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _make_record(vrp_mw, pc_vrp, sensor='MODIS_TERRA'):
    """Crea record mínimo para test."""
    return {
        'datetime_utc': '2026-04-23 01:50',
        'sensor': sensor,
        'vrp_mw': vrp_mw,
        'vrp_mir_mw': vrp_mw,
        'primary_cluster': {
            'vrp_mw': pc_vrp,
            'centroid_dist_km': 7.0,
            'n_pixels': 100,
        } if pc_vrp is not None else None,
        'hotspot_dist_km': 1.5,
        'anomaly_pixels': [],
        'product_version': 'standard',
    }


def test_sanity_cap_pc_garbage_filtered(tmp_path, monkeypatch):
    """Caso Lastarria: pc.vrp_mw=1.6M debe ser capeado a 0 + diag preservado."""
    import pipeline.store as store
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    rec = _make_record(vrp_mw=0, pc_vrp=1_639_629)
    store.append_record('LastarriaGarbageTest', rec, overwrite=True)

    recs = store.get_records('LastarriaGarbageTest')
    assert len(recs) == 1
    r = recs[0]
    assert r['primary_cluster']['vrp_mw'] == 0.0, 'pc.vrp_mw debe ser capeado a 0'
    assert r.get('diag_pc_rejected_sanity_cap_mw') == 1_639_629, 'Valor raw preservado'
    assert r.get('discarded_reason') == 'sanity_cap_pc_garbage', \
        'discarded_reason marcado cuando record.vrp_mw también 0'


def test_sanity_cap_pc_normal_record_unchanged(tmp_path, monkeypatch):
    """Record normal con pc.vrp_mw razonable (50 MW) NO debe ser capeado."""
    import pipeline.store as store
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    rec = _make_record(vrp_mw=50.0, pc_vrp=50.0)
    store.append_record('NormalRecord', rec, overwrite=True)

    r = store.get_records('NormalRecord')[0]
    assert r['primary_cluster']['vrp_mw'] == 50.0, 'pc.vrp_mw normal preservado'
    assert 'diag_pc_rejected_sanity_cap_mw' not in r


def test_sanity_cap_pc_threshold_boundary(tmp_path, monkeypatch):
    """Boundary: 49,999 MW pasa, 50,001 MW se capea."""
    import pipeline.store as store
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    # Bajo el cap
    rec_low = _make_record(vrp_mw=0, pc_vrp=49_999)
    store.append_record('Vol_LowCap', rec_low, overwrite=True)
    r_low = store.get_records('Vol_LowCap')[0]
    assert r_low['primary_cluster']['vrp_mw'] == 49_999

    # Sobre el cap
    rec_high = _make_record(vrp_mw=0, pc_vrp=50_001)
    store.append_record('Vol_HighCap', rec_high, overwrite=True)
    r_high = store.get_records('Vol_HighCap')[0]
    assert r_high['primary_cluster']['vrp_mw'] == 0.0
    assert r_high.get('diag_pc_rejected_sanity_cap_mw') == 50_001


def test_sanity_cap_pc_no_primary_cluster(tmp_path, monkeypatch):
    """Record sin primary_cluster no debe romper."""
    import pipeline.store as store
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    rec = _make_record(vrp_mw=2.5, pc_vrp=None)
    rec['primary_cluster'] = None
    store.append_record('NoPC', rec, overwrite=True)

    r = store.get_records('NoPC')[0]
    assert r['vrp_mw'] == 2.5
    assert 'diag_pc_rejected_sanity_cap_mw' not in r
