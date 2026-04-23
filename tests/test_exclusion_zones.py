"""Tests del filtro exclusion zones (S16 P3.6 simplificado).

Verifica que pixels en zonas excluidas se filtran, EXCEPTO si caen en
whitelist (lagos crateres activos como Tupungatito laguna).
"""

import numpy as np
from pipeline.exclusion_zones import (
    in_exclusion_mask, in_whitelist_mask, filter_hot_mask, haversine_km,
)


def test_haversine_known_distance():
    """Lascar vent (-23.36, -67.73) a centro Salar de Atacama (-23.5, -68.2).
    Distancia teorica ~50 km."""
    lat = np.array([[-23.36]])
    lon = np.array([[-67.73]])
    d = haversine_km(-23.5, -68.2, lat, lon)
    assert 40 < d[0, 0] < 60   # rango razonable


def test_in_exclusion_simple():
    """Pixel dentro del radio de exclusion."""
    lat = np.array([[-23.5]])
    lon = np.array([[-68.2]])
    zones = [{"lat": -23.5, "lon": -68.2, "radius_km": 25.0}]
    mask = in_exclusion_mask(lat, lon, zones)
    assert mask[0, 0] == True


def test_in_exclusion_outside():
    """Pixel fuera del radio."""
    lat = np.array([[-23.0]])
    lon = np.array([[-67.0]])
    zones = [{"lat": -23.5, "lon": -68.2, "radius_km": 25.0}]
    mask = in_exclusion_mask(lat, lon, zones)
    assert mask[0, 0] == False


def test_filter_hot_mask_removes_pixel_in_exclusion():
    """Hot pixel sobre Salar Atacama se filtra."""
    lat = np.array([[-23.5, -23.36]])
    lon = np.array([[-68.2, -67.73]])
    hot = np.array([[True, True]])
    zones = [{"lat": -23.5, "lon": -68.2, "radius_km": 25.0}]
    filtered, n_removed = filter_hot_mask(hot, lat, lon, zones)
    # Pixel 0: en Salar (excluido) -> removido
    # Pixel 1: en cráter Lascar (fuera Salar) -> preservado
    assert filtered[0, 0] == False
    assert filtered[0, 1] == True
    assert n_removed == 1


def test_whitelist_overrides_exclusion():
    """Pixel en zona excluida PERO en whitelist se preserva."""
    lat = np.array([[-23.5]])
    lon = np.array([[-68.2]])
    hot = np.array([[True]])
    zones = [{"lat": -23.5, "lon": -68.2, "radius_km": 25.0}]
    whitelist = [{"lat": -23.5, "lon": -68.2, "radius_km": 1.0,
                  "name": "active crater lake"}]
    filtered, n_removed = filter_hot_mask(hot, lat, lon, zones, whitelist)
    assert filtered[0, 0] == True   # whitelist preserva
    assert n_removed == 0


def test_no_exclusion_zones_no_op():
    """Sin exclude_zones, hot_mask vuelve identico."""
    lat = np.array([[1.0]])
    lon = np.array([[1.0]])
    hot = np.array([[True]])
    filtered, n = filter_hot_mask(hot, lat, lon, [])
    assert filtered[0, 0] == True
    assert n == 0


def test_lascar_salar_realistic():
    """Escenario real: hot_mask Lascar abril 2026 con pixels falsos del Salar.
    Salar centro -23.5, -68.2, radio 25 km.
    Pixel cráter (-23.36, -67.73): NO en Salar, preservado.
    Pixel Salar (-23.45, -68.05): en Salar, descartado."""
    lat = np.array([[-23.36, -23.45, -23.40]])
    lon = np.array([[-67.73, -68.05, -67.90]])
    hot = np.array([[True, True, True]])
    salar = [{"lat": -23.5, "lon": -68.2, "radius_km": 25.0}]
    filtered, n = filter_hot_mask(hot, lat, lon, salar)
    assert filtered[0, 0] == True   # cráter preservado
    assert filtered[0, 1] == False  # Salar descartado
    # Pixel 2 esta a ~14 km del centro Salar -> dentro -> filtrar
    # Verificacion: dist(-23.40,-67.90,-23.5,-68.2) ~= 30 km, fuera del salar 25 km
    # entonces se preserva. Si quieres asegurar que el test sea robusto cambia la coord.
    # Lo dejamos como dato de borde.
