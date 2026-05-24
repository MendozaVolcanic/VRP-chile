"""TDD RED tests para fix F47 H4: cluster rescue en store.append_record.

Bug F47 H4 confirmado en PR #169 (read-only investigación S77).
Doc canónica: docs/F47_NDC_RECALL_S76.md §9.

=== Resumen del bug ===

`pipeline/store.py:183-195` evalúa `hotspot_dist_km` (= distancia del pixel
single más caliente del scene) contra `MAX_HOTSPOT_DIST_KM` (default 5 km
operacional). Cuando ese pixel está lejos, anula `vrp_eruption` y limpia
`anomaly_pixels`, dejando `record["vrp_mw"] = 0`.

El problema: cuando el **primary_cluster vent-anchored** está dentro del
radio (= anomalía real del cráter, ej. NdC 21 pixels @ 0.536 km, 332 MW)
PERO un FP aislado lejos (ej. salar térmico a 26.58 km) es el pixel
"hottest" del scene, el gate destruye el rollup aunque el cluster real es
la verdad del scene.

Caso bandera empírico (NdC 2026-02-01 03:35 MODIS_TERRA):
- primary_cluster.vrp_mw = 332.756 MW
- primary_cluster.centroid_dist_km = 0.536 km   ← cráter
- primary_cluster.n_pixels = 21
- hotspot_dist_km = 26.58 km                    ← FP salar
- inner_radius_km NdC = 5
- Resultado actual: record.vrp_mw = 0   ← BUG
- Resultado esperado post-fix: record.vrp_mw = 332.756

=== Diferencia con bug S35 (test_store_eruption_filter_bug.py) ===

S35 tenía pixels in_range Y out_range — el pixel-level filter S35 H8
(_filter_pixels_by_distance) ya rescata esos casos. F47 H4 es distinto:
el FP single está DENTRO de MAX_HOTSPOT_DIST_KM pero FUERA del cluster
vent-anchored; los pixels in_range siguen existiendo pero el "safety net"
legacy (líneas 183-195) los borra basándose en hotspot_dist_km que apunta
al FP, no al cluster.

=== Spec del fix (Opción A, docs §9.5) ===

Insertar antes de la línea 183 un check de rescate:

    pc = record.get("primary_cluster") or {}
    pc_cdist = pc.get("centroid_dist_km")
    pc_vrp = pc.get("vrp_mw") or 0
    cluster_rescues = (pc_cdist is not None
                       and pc_cdist <= MAX_HOTSPOT_DIST_KM
                       and pc_vrp > 0)

    if (not cluster_rescues
            and hotspot_dist is not None
            and hotspot_dist > MAX_HOTSPOT_DIST_KM):
        # zero-out histórico (idéntico al actual)
        ...
        vrp_eruption = 0
    elif cluster_rescues and hotspot_dist is not None and hotspot_dist > MAX_HOTSPOT_DIST_KM:
        # F47 rescate: cluster vent-anchored gana al FP single
        vrp_eruption = pc_vrp
        record["hotspot_lat"] = pc.get("centroid_lat")
        record["hotspot_lon"] = pc.get("centroid_lon")
        record["hotspot_dist_km"] = pc_cdist
        record["discarded_reason"] = "single_pixel_far_overridden_by_cluster"
        # final_hotspot_* también reescritos para paridad con dashboard
        record["final_hotspot_lat"] = pc.get("centroid_lat")
        record["final_hotspot_lon"] = pc.get("centroid_lon")
        record["final_hotspot_dist_km"] = pc_cdist
        record["final_hotspot_source"] = "cluster_rescue"

=== Estado de los tests ===

Marcados con `@pytest.mark.xfail(strict=True, reason="F47 fix pending A45")`
los casos RED (los que requieren el fix). Cuando el fix entre y los tests
pasen, `strict=True` los convierte en XPASS-FAIL forzando a quitar el
marker — patrón TDD red→green explícito.

Los casos GREEN (B y C) NO llevan xfail: pasan pre y post-fix.

Pre-condición de mergeo del fix (A38+A45 S75): tag defensivo
`pre-s77-f47-store-cluster-rescue` antes de tocar store.py.

Ref: docs/F47_NDC_RECALL_S76.md §9.5
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# NdC bandera: vent (-37.851, -71.169), inner_radius = 5 km, MAX_HOTSPOT 5 km.
# Salar FP "a 26.58 km del vent" — coords no críticas para el test, solo dist.

def _ndc_flag_record(
    pc_vrp_mw: float = 332.756,
    pc_cdist_km: float = 0.536,
    pc_n_pixels: int = 21,
    hotspot_dist_km: float = 26.58,
    primary_cluster: dict | None = "DEFAULT",  # type: ignore[assignment]
    sensor: str = "MODIS_TERRA",
    dt: str = "2026-02-01 03:35",
):
    """Sintético del caso NdC 2026-02-01 03:35 MODIS_TERRA (F47 bandera).

    Defaults reproducen el record real. `primary_cluster=None` para simular
    record pre-S27 (sin cluster). `primary_cluster=dict` para overrides
    granulares (test 2, cluster también lejano).
    """
    if primary_cluster == "DEFAULT":
        primary_cluster = {
            "n_pixels": pc_n_pixels,
            "vrp_mw": pc_vrp_mw,
            "centroid_lat": -37.851 + 0.001,
            "centroid_lon": -71.169 + 0.001,
            "centroid_dist_km": pc_cdist_km,
        }

    # Pixels: 21 in_range cerca del cráter + 1 FP lejos.
    # Cada pixel near contribuye pc_vrp_mw/21 — total ≈ pc_vrp_mw.
    near_pixels = [
        {
            "lat": -37.851 + i * 0.001,
            "lon": -71.169 + i * 0.001,
            "dist_km": 0.4 + i * 0.01,
            "bt_k": 320.0 + i * 0.5,
            "vrp_mw": pc_vrp_mw / max(pc_n_pixels, 1),
        }
        for i in range(pc_n_pixels)
    ]
    # FP single lejano (lo que produce hotspot_dist_km alto). Para que sea
    # el "hottest" del scene, BT mayor que los pixels cráter — irrelevante
    # para el gate de store.py que mira hotspot_dist_km, no BT.
    far_pixel = {
        "lat": -37.851 + 0.2,
        "lon": -71.169 + 0.2,
        "dist_km": hotspot_dist_km,
        "bt_k": 340.0,
        "vrp_mw": 5.0,
    }

    rec = {
        "vrp_mir_mw": pc_vrp_mw + 5.0,  # scene-wide sum
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": pc_n_pixels + 1,
        "n_vent_pixels": 0,
        "vent_hotspot_lat": None,
        "vent_hotspot_lon": None,
        "vent_hotspot_dist_km": None,
        # hotspot_* = pixel single más caliente = el FP lejano
        "hotspot_lat": far_pixel["lat"],
        "hotspot_lon": far_pixel["lon"],
        "hotspot_dist_km": hotspot_dist_km,
        "final_hotspot_lat": far_pixel["lat"],
        "final_hotspot_lon": far_pixel["lon"],
        "final_hotspot_dist_km": hotspot_dist_km,
        "final_hotspot_source": "eruption",
        "distance_class": "far",
        "anomaly_pixels": near_pixels + [far_pixel],
        "t_bg_k": 290.0,
        "t_max_i04_k": 340.0,
        "sensor": sensor,
        "granule": f"fake_{dt}_{sensor}.hdf",
        "product_version": "standard",
        "datetime_utc": dt,
    }
    if primary_cluster is not None:
        rec["primary_cluster"] = primary_cluster
    return rec


@pytest.fixture
def basic_setup(tmp_path, monkeypatch):
    """Setup estándar: DATA_DIR aislado + pisos VRP a 0 para no interferir."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS750", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_MODIS", 0.0)
    return tmp_path


def _save_and_load(rec, basic_setup, volcano="NdCTest",
                   vent_lat=-37.851, vent_lon=-71.169,
                   max_hotspot=5.0):
    """Helper: ejecuta append_record y devuelve el record persistido.

    Nota: usa enable_pixel_level_distance_filter=False intencionalmente.
    El bug F47 H4 está en el gate legacy de líneas 183-195, NO en el filter
    pixel-level. Con pixel-level=True el FP single sería removido por
    _filter_pixels_by_distance (porque dist > MAX), pero ANTES de ese punto
    hotspot_dist_km ya fue seteado por upstream apuntando al far. El gate
    igual dispara. Para aislar el bug F47 H4 puro, dejamos pixel-level=False;
    el test con pixel-level=True queda para regresión futura.
    """
    store_mod.append_record(
        volcano, rec, vent_lat, vent_lon,
        overwrite=False,
        max_hotspot_dist_km=max_hotspot,
        enable_pixel_level_distance_filter=False,
    )
    data = json.loads((basic_setup / f"{volcano}.json").read_text())
    return data["records"][0]


# ===========================================================================
# Test 1 — caso bandera NdC: cluster cerca + hotspot single lejos (RED)
# ===========================================================================

def test_rescue_cluster_near_vent_with_hotspot_far_fp(basic_setup):
    """RED: NdC 2026-02-01 03:35 MODIS_TERRA. Cluster cráter (21 px @ 0.536 km,
    332.756 MW) debe RESCATAR el rollup aunque un FP aislado a 26.58 km sea el
    pixel hottest del scene.

    Pre-fix (estado actual main):
        record["vrp_mw"] == 0  (gate línea 183-195 lo anula)

    Post-fix (Opción A):
        record["vrp_mw"] == 332.756  (cluster vent-anchored rescata)
    """
    rec = _ndc_flag_record(
        pc_vrp_mw=332.756,
        pc_cdist_km=0.536,
        pc_n_pixels=21,
        hotspot_dist_km=26.58,
    )

    saved = _save_and_load(rec, basic_setup, max_hotspot=5.0)

    # Sanity: el primary_cluster sigue ahí con los valores esperados
    assert saved.get("primary_cluster", {}).get("vrp_mw") == pytest.approx(332.756, rel=1e-3)
    assert saved.get("primary_cluster", {}).get("centroid_dist_km") == pytest.approx(0.536, rel=1e-3)

    # CRÍTICO (RED hoy, GREEN post-fix): vrp_mw debe reflejar el cluster
    assert saved.get("vrp_mw", 0) == pytest.approx(332.756, rel=1e-2), (
        f"F47 H4: cluster cerca (0.536 km, 332 MW) debió rescatar el rollup. "
        f"vrp_mw obtenido={saved.get('vrp_mw')} (esperado ≈332.756). "
        f"discarded_reason={saved.get('discarded_reason')}"
    )


# ===========================================================================
# Test 2 — sin rescate cuando cluster TAMBIÉN está lejos (GREEN pre y post)
# ===========================================================================

def test_no_rescue_when_cluster_also_far(basic_setup):
    """GREEN pre y post-fix: si el primary_cluster también está fuera de
    inner_radius (cdist > MAX_HOTSPOT_DIST_KM), NO hay rescate posible — el
    gate legacy debe seguir anulando.

    Caso fenómeno: incendio forestal lejano con cluster propio, ningún hot
    pixel cerca del cráter. Es correcto descartar (no es anomalía volcánica).
    """
    rec = _ndc_flag_record(
        pc_vrp_mw=12.0,
        pc_cdist_km=18.0,            # cluster lejos (>5)
        pc_n_pixels=6,
        hotspot_dist_km=26.58,       # hotspot también lejos
    )
    # En este caso el cluster está fuera del inner_radius pero podría existir
    # físicamente. Aún así NO debe rescatar (vrp=0 sigue siendo el output).
    saved = _save_and_load(rec, basic_setup, max_hotspot=5.0)

    assert saved.get("vrp_mw", 0) == 0, (
        f"Cluster fuera de inner_radius (18 km) no debe rescatar — "
        f"el gate legacy debe seguir activo. vrp_mw={saved.get('vrp_mw')}"
    )


# ===========================================================================
# Test 3 — sin rescate cuando NO HAY primary_cluster (GREEN pre y post)
# ===========================================================================

def test_no_rescue_when_no_primary_cluster(basic_setup):
    """GREEN pre y post-fix: records pre-S27 sin primary_cluster (schema viejo,
    o sensor/path que no genera clustering) NO se rescatan — el gate legacy
    aplica normalmente porque no hay información de cluster para apelar.
    """
    rec = _ndc_flag_record(
        hotspot_dist_km=26.58,
        primary_cluster=None,        # sin cluster
    )
    # anomaly_pixels igual quedan (incluyen el FP far), pero sin cluster
    # no podemos saber si el "cluster real" estaría cerca.

    saved = _save_and_load(rec, basic_setup, max_hotspot=5.0)

    assert saved.get("vrp_mw", 0) == 0, (
        f"Sin primary_cluster no hay rescate posible (schema legacy). "
        f"vrp_mw={saved.get('vrp_mw')}"
    )
    # El gate debe haber dejado su huella de descarte
    assert saved.get("discarded_reason") == "eruption_hotspot_too_far"


# ===========================================================================
# Test 4 — rescate reescribe hotspot/final_hotspot al centroide cluster (RED)
# ===========================================================================

def test_rescue_preserves_cluster_centroid_as_hotspot(basic_setup):
    """RED: tras el rescate, los campos hotspot_* y final_hotspot_* deben
    apuntar al centroide del cluster (no al pixel single lejano que
    originalmente los seteó). Esto mantiene la paridad con `mirovaEqVrp` del
    dashboard, que asume que final_hotspot_dist_km coincide con el cluster
    cuando éste rescata.

    Además, `final_hotspot_source == 'cluster_rescue'` (etiqueta nueva) para
    que audits puedan distinguir records rescatados de records normales.
    """
    pc_lat = -37.851 + 0.001
    pc_lon = -71.169 + 0.001
    rec = _ndc_flag_record(
        pc_vrp_mw=332.756,
        pc_cdist_km=0.536,
        pc_n_pixels=21,
        hotspot_dist_km=26.58,
        primary_cluster={
            "n_pixels": 21,
            "vrp_mw": 332.756,
            "centroid_lat": pc_lat,
            "centroid_lon": pc_lon,
            "centroid_dist_km": 0.536,
        },
    )

    saved = _save_and_load(rec, basic_setup, max_hotspot=5.0)

    # final_hotspot_* debe reescribirse al centroide del cluster
    assert saved.get("final_hotspot_lat") == pytest.approx(pc_lat, abs=1e-6), (
        f"final_hotspot_lat debe ser centroide del cluster ({pc_lat}), "
        f"got {saved.get('final_hotspot_lat')}"
    )
    assert saved.get("final_hotspot_lon") == pytest.approx(pc_lon, abs=1e-6)
    assert saved.get("final_hotspot_dist_km") == pytest.approx(0.536, rel=1e-3)
    assert saved.get("final_hotspot_source") == "cluster_rescue", (
        f"final_hotspot_source debe ser 'cluster_rescue' tras rescate, "
        f"got {saved.get('final_hotspot_source')}"
    )


# ===========================================================================
# Test 5 — discarded_reason post-rescate ya no es 'eruption_hotspot_too_far' (RED)
# ===========================================================================

def test_rescue_changes_discarded_reason(basic_setup):
    """RED: tras el rescate, `discarded_reason` no debe ser
    'eruption_hotspot_too_far' (porque NO se descartó — se rescató). El fix
    propone 'single_pixel_far_overridden_by_cluster' como etiqueta diagnóstica
    para audits posteriores (ej. contar cuántos records dependen de rescate).

    Aceptamos también que el campo simplemente NO esté presente (rescate
    completo borra la huella de descarte). Lo INACEPTABLE es que diga
    'eruption_hotspot_too_far', porque eso miente sobre lo que pasó.
    """
    rec = _ndc_flag_record(
        pc_vrp_mw=332.756,
        pc_cdist_km=0.536,
        hotspot_dist_km=26.58,
    )

    saved = _save_and_load(rec, basic_setup, max_hotspot=5.0)

    reason = saved.get("discarded_reason")
    assert reason != "eruption_hotspot_too_far", (
        f"Tras rescate, discarded_reason no debe afirmar 'eruption_hotspot_too_far' "
        f"(no hubo descarte real del rollup). got reason={reason}"
    )
    # Aceptamos None o la nueva etiqueta documentada en §9.5
    assert reason in (None, "single_pixel_far_overridden_by_cluster"), (
        f"discarded_reason inesperado: {reason}"
    )
