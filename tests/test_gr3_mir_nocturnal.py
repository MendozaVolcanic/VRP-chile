"""G-R3 (S88 Frente C) — coverage de robustez: MIR solo nocturno.

Tests OFFLINE de robustez. NO tocan el pipeline de producción.

Fenómeno físico: la banda MIR (3.7-4.05 µm) mide radiancia que de día está
contaminada por reflexión solar — el Sol emite fuertemente en ese rango, así
que un pixel diurno parece "caliente" aunque no haya actividad volcánica. Por
eso MIROVA (y nuestro clon) solo computa VRP en pasadas nocturnas. El gate
físico es la elevación solar: si el Sol está bajo el horizonte (elevación < 0°)
es de noche y el dato es usable.

Mecanismo del pipeline: hay DOS implementaciones de la elevación solar,
verificadas en el código fuente (S88):
  - scripts/run_pipeline.py:68  solar_elevation(lat, lon, dt_utc) -> grados
    + run_pipeline.py:92        is_nighttime(...) -> bool (elev < 0)
    Se usa al construir records (run_pipeline.py:141-143) para clasificar
    día/noche antes de procesar.
  - pipeline/store.py:47        _solar_elevation(lat, lon, dt_utc) -> grados
    Red de seguridad: append_record rechaza records diurnos
    (store.py: "STORE REJECT daytime" usando _solar_elevation).

Ambas usan la aproximación de declinación de Spencer (1971). Estos tests
ejercen las funciones puras con un volcán chileno real (Lascar, Andes
centrales) a mediodía y medianoche locales, verificando el signo de la
elevación — que es lo que el gate día/noche consume.
"""
from __future__ import annotations

import importlib
from datetime import datetime

import pytest


# Lascar (Tier A, 100% nocturno MIR): Andes centrales, hemisferio sur.
LASCAR_LAT = -23.37
LASCAR_LON = -67.73

# La hora solar local que usan las funciones es: hour_utc + lon/15.
# Para lon=-67.73 el offset solar es -4.515 h respecto a UTC. Por eso:
#   - mediodía solar local (~12:00) ≈ 16:31 UTC  → Sol arriba (elev > 0).
#   - medianoche solar local (~00:00) ≈ 04:31 UTC → Sol abajo (elev < 0).
# Usamos un día de verano austral (enero) y otro de invierno (julio) para no
# depender de una estación particular: de noche la elevación es < 0 todo el año.
MIDDAY_UTC = datetime(2026, 1, 15, 16, 31)
MIDNIGHT_UTC = datetime(2026, 1, 15, 4, 31)
MIDDAY_WINTER_UTC = datetime(2026, 7, 15, 16, 31)
MIDNIGHT_WINTER_UTC = datetime(2026, 7, 15, 4, 31)


# --- Importación de las dos implementaciones reales del gate ---
run_pipeline = importlib.import_module("scripts.run_pipeline")
store = importlib.import_module("pipeline.store")


# ----------------------------------------------------------------------------
# run_pipeline.solar_elevation — el gate primario al construir records.
# ----------------------------------------------------------------------------
def test_run_pipeline_midday_sun_above_horizon():
    elev = run_pipeline.solar_elevation(LASCAR_LAT, LASCAR_LON, MIDDAY_UTC)
    assert elev > 0.0, "mediodía solar local debe dar elevación positiva"


def test_run_pipeline_midnight_sun_below_horizon():
    elev = run_pipeline.solar_elevation(LASCAR_LAT, LASCAR_LON, MIDNIGHT_UTC)
    assert elev < 0.0, "medianoche solar local debe dar elevación negativa"


def test_run_pipeline_midnight_below_horizon_in_winter():
    """De noche el Sol está bajo el horizonte en cualquier estación."""
    elev = run_pipeline.solar_elevation(LASCAR_LAT, LASCAR_LON, MIDNIGHT_WINTER_UTC)
    assert elev < 0.0


def test_run_pipeline_midday_above_horizon_in_winter():
    elev = run_pipeline.solar_elevation(LASCAR_LAT, LASCAR_LON, MIDDAY_WINTER_UTC)
    assert elev > 0.0


# ----------------------------------------------------------------------------
# is_nighttime — wrapper booleano del gate (elev < 0).
# ----------------------------------------------------------------------------
def test_is_nighttime_true_at_midnight():
    assert run_pipeline.is_nighttime(LASCAR_LAT, LASCAR_LON, MIDNIGHT_UTC) is True


def test_is_nighttime_false_at_midday():
    assert run_pipeline.is_nighttime(LASCAR_LAT, LASCAR_LON, MIDDAY_UTC) is False


def test_is_nighttime_consistent_with_solar_elevation_sign():
    """is_nighttime es exactamente (solar_elevation < 0). Contrato del gate."""
    for dt in (MIDDAY_UTC, MIDNIGHT_UTC, MIDDAY_WINTER_UTC, MIDNIGHT_WINTER_UTC):
        elev = run_pipeline.solar_elevation(LASCAR_LAT, LASCAR_LON, dt)
        assert run_pipeline.is_nighttime(LASCAR_LAT, LASCAR_LON, dt) == (elev < 0.0)


# ----------------------------------------------------------------------------
# store._solar_elevation — la red de seguridad que rechaza records diurnos.
# Debe dar el MISMO signo que el gate primario (misma aproximación Spencer).
# ----------------------------------------------------------------------------
def test_store_solar_elevation_midday_positive():
    elev = store._solar_elevation(LASCAR_LAT, LASCAR_LON, MIDDAY_UTC)
    assert elev > 0.0


def test_store_solar_elevation_midnight_negative():
    """El gate de store (append_record rechaza si elev >= 0) ve la noche como
    elevación negativa → record nocturno NO se rechaza."""
    elev = store._solar_elevation(LASCAR_LAT, LASCAR_LON, MIDNIGHT_UTC)
    assert elev < 0.0


def test_store_and_run_pipeline_agree_on_sign():
    """Las dos implementaciones del gate coinciden en el signo (día/noche)
    para los cuatro casos canónicos — si divergen, el record podría pasar el
    gate primario y ser rechazado por la red de seguridad (o viceversa)."""
    for dt in (MIDDAY_UTC, MIDNIGHT_UTC, MIDDAY_WINTER_UTC, MIDNIGHT_WINTER_UTC):
        e_store = store._solar_elevation(LASCAR_LAT, LASCAR_LON, dt)
        e_run = run_pipeline.solar_elevation(LASCAR_LAT, LASCAR_LON, dt)
        assert (e_store < 0.0) == (e_run < 0.0), f"signo discrepante en {dt}"
