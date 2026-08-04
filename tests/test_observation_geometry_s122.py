"""S122 — geometría de observación persistida (sensor/solar zenith+azimuth).

POR QUÉ estos tests: el helper corre dentro de los 3 procesadores del NRT sobre
granules reales heterogéneos (productos que a veces no traen un ángulo, arrays con
NaN de relleno, formas inconsistentes). Un fallo suyo NO debe tumbar una corrida:
el contrato es "devolvé None en esa clave, nunca lances".
"""
import numpy as np
import pytest

from pipeline.scan_geometry import OBSERVATION_ANGLE_KEYS, observation_geometry


def _grid():
    """Escena 3x3 sintética: lat 0..2 (norte→sur), lon 10..12."""
    lat = np.array([[2.0, 2.0, 2.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]])
    lon = np.array([[10.0, 11.0, 12.0]] * 3)
    return lat, lon


def _angles():
    sz = np.array([[10.0, 20.0, 30.0], [11.0, 21.0, 31.0], [12.0, 22.0, 32.0]])
    return {
        "sensor_zenith_deg": sz,
        "sensor_azimuth_deg": sz + 100.0,
        "solar_zenith_deg": sz + 40.0,
        "solar_azimuth_deg": sz + 200.0,
    }


def test_samples_nearest_pixel():
    lat, lon = _grid()
    # Punto pegado al píxel central (1.0, 11.0) → fila 1, col 1.
    got = observation_geometry(lat, lon, _angles(), 1.05, 10.98)
    assert got["sensor_zenith_deg"] == 21.0
    assert got["sensor_azimuth_deg"] == 121.0
    assert got["solar_zenith_deg"] == 61.0
    assert got["solar_azimuth_deg"] == 221.0


def test_all_keys_always_present():
    """El schema del record no debe cambiar de forma según el granule."""
    lat, lon = _grid()
    got = observation_geometry(lat, lon, {"sensor_zenith_deg": _angles()["sensor_zenith_deg"]},
                               1.0, 11.0)
    assert set(got) == set(OBSERVATION_ANGLE_KEYS)
    assert got["sensor_zenith_deg"] == 21.0
    assert got["solar_zenith_deg"] is None  # ausente en el producto → None, no error


@pytest.mark.parametrize("angles", [None, {}, {"sensor_zenith_deg": None}])
def test_missing_angles_return_none(angles):
    lat, lon = _grid()
    got = observation_geometry(lat, lon, angles, 1.0, 11.0)
    assert all(v is None for v in got.values())


def test_no_target_returns_none():
    """Record sin hotspot resuelto (final_hotspot None) → sin geometría, sin crash."""
    lat, lon = _grid()
    assert all(v is None for v in observation_geometry(lat, lon, _angles(), None, None).values())


def test_shape_mismatch_is_ignored_not_fatal():
    lat, lon = _grid()
    bad = {"sensor_zenith_deg": np.array([[1.0, 2.0]])}  # forma distinta
    assert observation_geometry(lat, lon, bad, 1.0, 11.0)["sensor_zenith_deg"] is None


def test_nan_fill_values_do_not_break_selection():
    """Los productos usan NaN/-999 de relleno; el píxel elegido debe ser válido."""
    lat, lon = _grid()
    lat = lat.copy()
    lat[0, :] = np.nan  # fila superior sin geolocalización
    got = observation_geometry(lat, lon, _angles(), 1.0, 11.0)
    assert got["sensor_zenith_deg"] == 21.0


def test_nan_angle_value_yields_none():
    lat, lon = _grid()
    ang = _angles()
    ang["sensor_zenith_deg"] = ang["sensor_zenith_deg"].copy()
    ang["sensor_zenith_deg"][1, 1] = np.nan
    got = observation_geometry(lat, lon, ang, 1.0, 11.0)
    assert got["sensor_zenith_deg"] is None
    assert got["sensor_azimuth_deg"] == 121.0  # las demás siguen resolviendo
