"""TDD para bug S35: store.append_record descarta cluster cercano cuando coexiste
pixel lejano más caliente.

Bug detectado 2026-05-10 al hacer R2 sobre Puyehue lacolito 05:42:02:
- VRP-chile detectó 35 pixels en zona lacolito (6-9 km, dentro inner_radius=20)
- Pixel más caliente individual estaba a 25.15 km (probable fuego/incendio)
- store.py línea 119 descarta TODA anomaly_pixels porque hotspot_dist (= dist
  del pixel más caliente) > radius_km
- Resultado: lacolito perdido, vrp_mw=0 aunque vrp_mir_mw=5.07

Reach del bug en 30d: 426 records descartados en 11 Tier A, ~20 confirmados
como pérdida de ALERTA_TERMICA reportada por MIROVA con pixels en zona summit.

Casos test:
- A: cluster cercano (k pixels en zona summit) + pixel lejano > radius
     → debe PRESERVAR cluster cercano (ahora FALLA)
- B: solo pixel lejano sin cluster cercano
     → debe descartar (comportamiento histórico OK, regression check)
- C: cluster lejano sin nada cercano
     → preserva pero distance_class='far' (MIROVA literal cierre S33+)
- D: ambos clusters, cercano más débil que lejano
     → preserva cercano + agnóstico de lejano
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod


def _record_with_mixed_pixels(dt="2026-04-15 05:42",
                              sensor="VIIRS_NOAA21",
                              n_summit=35,
                              n_far=1,
                              vrp_summit_each=0.005,
                              vrp_far_each=2.7,
                              far_dist_km=29.0):
    """Record sintético: n_summit pixels @ 7-8km del centro + n_far pixel(s) @ far_dist_km.

    El "primary cluster" será el cercano (más pixels) según geometría natural,
    pero `hotspot_dist_km` será el del pixel más caliente individual = far.
    """
    summit_pixels = [{"lat": -40.52 + i*0.001, "lon": -72.14 + i*0.001,
                      "dist_km": 7.5 + i*0.05, "bt_k": 274.0 + i*0.1,
                      "vrp_mw": vrp_summit_each}
                     for i in range(n_summit)]
    far_pixels = [{"lat": -40.36, "lon": -72.07, "dist_km": far_dist_km,
                   "bt_k": 285.0, "vrp_mw": vrp_far_each}
                  for _ in range(n_far)]
    all_pixels = summit_pixels + far_pixels

    total_vrp = sum(p["vrp_mw"] for p in all_pixels)
    # primary cluster representa el cercano (cluster grande)
    primary_cluster = {
        "n_pixels": n_summit, "vrp_mw": n_summit * vrp_summit_each,
        "centroid_lat": -40.523, "centroid_lon": -72.142,
        "centroid_dist_km": 7.5,
    }

    return {
        "vrp_mir_mw": total_vrp,
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": len(all_pixels),
        "n_vent_pixels": 0,
        "vent_hotspot_lat": None, "vent_hotspot_lon": None, "vent_hotspot_dist_km": None,
        # hotspot_* = pixel más caliente individual (que es el far)
        "hotspot_lat": -40.36, "hotspot_lon": -72.07, "hotspot_dist_km": far_dist_km,
        "final_hotspot_lat": -40.36, "final_hotspot_lon": -72.07,
        "final_hotspot_dist_km": far_dist_km, "final_hotspot_source": "eruption",
        "distance_class": "summit",  # derived earlier in pipeline
        "anomaly_pixels": all_pixels,
        "primary_cluster": primary_cluster,
        "t_bg_k": 270.0, "t_max_i04_k": 285.0,
        "sensor": sensor, "granule": f"fake_{dt}_{sensor}.nc",
        "product_version": "standard", "datetime_utc": dt,
    }


@pytest.fixture
def basic_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS750", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_MODIS", 0.0)
    return tmp_path


# ===========================================================================
# CASO A — el bug específico que descubrimos en Puyehue lacolito
# ===========================================================================

def test_A_cluster_cercano_se_preserva_aunque_haya_pixel_lejano(basic_setup):
    """Bug S35: 35 pixels @ 7.5km (cluster summit) + 1 pixel @ 29km (FP/incendio).
    El cluster cercano debe preservarse y vrp_mw debe reflejar su VRP.

    Reproducción exacta caso Puyehue 2026-05-09 05:42 lacolito:
    - 35 pixels @ ~7.5km (lacolito real)
    - 1 pixel @ 29km (probable incendio)
    - radius_km=25 (Puyehue)
    """
    rec = _record_with_mixed_pixels(
        n_summit=35, vrp_summit_each=0.005,  # 35 * 0.005 = 0.175 MW (≈ MIROVA report 0.18)
        n_far=1, vrp_far_each=2.7, far_dist_km=29.0,
    )

    store_mod.append_record("PuyehueTest", rec, -40.59, -72.117,
                            overwrite=False, max_hotspot_dist_km=25.0, enable_pixel_level_distance_filter=True)

    data = json.loads((basic_setup / "PuyehueTest.json").read_text())
    saved = data["records"][0]

    # CRÍTICO: vrp_mw debe ser >0 (cluster cercano preservado)
    # MIROVA reportó VRP=0.18 MW para lacolito; esperamos algo similar (~0.175)
    assert saved.get("vrp_mw", 0) > 0, (
        f"BUG S35: vrp_mw=0 cuando hay 35 pixels válidos en zona summit. "
        f"discarded_reason={saved.get('discarded_reason')}, "
        f"vrp_mir_mw={saved.get('vrp_mir_mw')}"
    )
    # Razonable: vrp_mw debe estar cerca del VRP del cluster cercano
    assert 0.10 <= saved.get("vrp_mw", 0) <= 1.0, (
        f"vrp_mw={saved.get('vrp_mw')} fuera de rango esperado"
    )


def test_A2_lascar_caso_real_2026_04_23(basic_setup):
    """Reproducción exacta caso Lascar 2026-04-23 04:48:
    MIROVA reportó 0.13 MW @ 1.5km (cráter Lascar).
    VRP-chile descartó 38/40 pixels en zona del cráter porque hotspot (más
    caliente) estaba a 29.0 km.
    """
    # 40 pixels @ ~1.5km del centro (cluster cráter)
    summit_pixels = [{"lat": -23.37 + i*0.001, "lon": -67.74 + i*0.001,
                      "dist_km": 1.0 + i*0.05, "bt_k": 280.0 + i*0.1,
                      "vrp_mw": 0.003}
                     for i in range(40)]
    # 2 pixels lejanos (Salar térmico)
    far_pixels = [{"lat": -23.10, "lon": -67.45, "dist_km": 29.0,
                   "bt_k": 290.0, "vrp_mw": 0.5} for _ in range(2)]

    rec = {
        "vrp_mir_mw": 1.35,  # MIROVA actually report says ~1.35 vrp_mir
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": 42, "n_vent_pixels": 0,
        "vent_hotspot_lat": None, "vent_hotspot_lon": None, "vent_hotspot_dist_km": None,
        "hotspot_lat": -23.10, "hotspot_lon": -67.45, "hotspot_dist_km": 29.0,
        "final_hotspot_lat": -23.10, "final_hotspot_lon": -67.45,
        "final_hotspot_dist_km": 29.0, "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "anomaly_pixels": summit_pixels + far_pixels,
        "primary_cluster": {"n_pixels": 40, "vrp_mw": 0.12,
                            "centroid_lat": -23.37, "centroid_lon": -67.74,
                            "centroid_dist_km": 1.5},
        "t_bg_k": 275.0, "t_max_i04_k": 290.0,
        "sensor": "VIIRS_NOAA20", "granule": "fake.nc",
        "product_version": "standard", "datetime_utc": "2026-04-23 04:48",
    }

    store_mod.append_record("LascarTest", rec, -23.37, -67.74,
                            overwrite=False, max_hotspot_dist_km=25.0, enable_pixel_level_distance_filter=True)

    data = json.loads((basic_setup / "LascarTest.json").read_text())
    saved = data["records"][0]

    assert saved.get("vrp_mw", 0) > 0, (
        f"BUG: Lascar 04-23 alerta MIROVA 0.13MW perdida. "
        f"40 pixels en cráter descartados por 2 pixels lejanos. "
        f"discarded_reason={saved.get('discarded_reason')}"
    )


# ===========================================================================
# CASO B — comportamiento legacy debe preservarse (regression check)
# ===========================================================================

def test_B_solo_pixel_lejano_debe_descartarse(basic_setup):
    """Sin cluster cercano, solo 1 pixel a 29km → comportamiento histórico OK
    (descartar). Este test garantiza que el fix no rompe el caso correcto.
    """
    rec = _record_with_mixed_pixels(
        n_summit=0, vrp_summit_each=0,  # NO cluster cercano
        n_far=1, vrp_far_each=2.7, far_dist_km=29.0,
    )
    rec["primary_cluster"] = {"n_pixels": 1, "vrp_mw": 2.7,
                              "centroid_lat": -40.36, "centroid_lon": -72.07,
                              "centroid_dist_km": 29.0}

    store_mod.append_record("FarOnlyTest", rec, -40.59, -72.117,
                            overwrite=False, max_hotspot_dist_km=25.0, enable_pixel_level_distance_filter=True)

    data = json.loads((basic_setup / "FarOnlyTest.json").read_text())
    saved = data["records"][0]

    # Sin cluster summit, no debería haber detección summit
    # vrp_mw=0 OR distance_class=far es aceptable
    if saved.get("vrp_mw", 0) > 0:
        assert saved.get("distance_class") == "far", (
            "Si vrp_mw>0 con solo pixel lejano, debe ser class=far"
        )


# ===========================================================================
# CASO C — cluster lejano sin cercano (MIROVA literal cierre S33+)
# ===========================================================================

def test_C_cluster_lejano_se_preserva_como_far(basic_setup):
    """MIROVA reporta clusters far como detecciones válidas con
    distance_class=far (cierre S33+). Cluster lejano de 10 pixels NO debe
    desaparecer; debe quedar marcado como class=far.

    Nota: este test puede pasar o no según política de filtros.
    Lo dejamos como spec del comportamiento MIROVA-aligned.
    """
    far_pixels = [{"lat": -40.36 + i*0.001, "lon": -72.07,
                   "dist_km": 28.0 + i*0.1, "bt_k": 285.0,
                   "vrp_mw": 0.5} for i in range(10)]

    rec = {
        "vrp_mir_mw": 5.0, "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": 10, "n_vent_pixels": 0,
        "vent_hotspot_lat": None, "vent_hotspot_lon": None, "vent_hotspot_dist_km": None,
        "hotspot_lat": -40.36, "hotspot_lon": -72.07, "hotspot_dist_km": 28.5,
        "final_hotspot_lat": -40.36, "final_hotspot_lon": -72.07,
        "final_hotspot_dist_km": 28.5, "final_hotspot_source": "eruption",
        "distance_class": "far",
        "anomaly_pixels": far_pixels,
        "primary_cluster": {"n_pixels": 10, "vrp_mw": 5.0,
                            "centroid_lat": -40.36, "centroid_lon": -72.07,
                            "centroid_dist_km": 28.5},
        "t_bg_k": 275.0, "t_max_i04_k": 285.0,
        "sensor": "VIIRS_NOAA20", "granule": "fake.nc",
        "product_version": "standard", "datetime_utc": "2026-04-15 05:42",
    }

    store_mod.append_record("FarClusterTest", rec, -40.59, -72.117,
                            overwrite=False, max_hotspot_dist_km=25.0, enable_pixel_level_distance_filter=True)

    data = json.loads((basic_setup / "FarClusterTest.json").read_text())
    saved = data["records"][0]

    # Política propuesta MIROVA-literal: preservar pero clase=far
    # (este test puede quedar como soft-fail dependiendo de la decisión final)
    # Por ahora, al menos validamos que la información NO se pierde sin trazas
    assert saved.get("discarded_anomaly_pixels") or saved.get("anomaly_pixels"), (
        "Cluster lejano debe preservarse en algún campo (anomaly_pixels o discarded_*)"
    )


# ===========================================================================
# CASO D — ambos clusters, validación composición
# ===========================================================================

def test_D_cluster_cercano_debil_mas_cluster_lejano_fuerte(basic_setup):
    """Caso compuesto: cluster cercano pequeño (5 pixels, 0.05 MW) + cluster
    lejano grande (20 pixels, 10 MW). El comportamiento esperado:
    - Cluster cercano preservado como summit
    - Cluster lejano preservado como far (NO suma al summit)
    """
    rec = _record_with_mixed_pixels(
        n_summit=5, vrp_summit_each=0.01,
        n_far=20, vrp_far_each=0.5, far_dist_km=29.0,
    )
    rec["primary_cluster"] = {"n_pixels": 5, "vrp_mw": 0.05,
                              "centroid_lat": -40.523, "centroid_lon": -72.142,
                              "centroid_dist_km": 7.5}

    store_mod.append_record("MixedTest", rec, -40.59, -72.117,
                            overwrite=False, max_hotspot_dist_km=25.0, enable_pixel_level_distance_filter=True)

    data = json.loads((basic_setup / "MixedTest.json").read_text())
    saved = data["records"][0]

    # vrp_mw debe reflejar el cluster summit (cercano), no el lejano
    # Esperado ≈ 0.05 MW, NO 10 MW (cluster lejano sumado erróneamente)
    vrp_final = saved.get("vrp_mw", 0)
    assert 0 < vrp_final < 1.0, (
        f"vrp_mw={vrp_final} debe reflejar cluster summit (~0.05 MW), "
        f"no cluster lejano completo"
    )
