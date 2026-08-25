"""S124 — overrides de configuración de volcán POR PERFIL.

El problema: la geometría de cada volcán (`vent_lat/lon`, `inner_radius_km`,
`radius_km`) vive en `volcanoes.yaml`, que es ÚNICO y compartido por todos los
perfiles. Hasta ahora no había forma de decir "en el perfil experimental quiero
mirar solo 1 km alrededor del cráter de Nevados de Chillán" sin cambiarlo
también para el producto operacional — que es exactamente lo que no se puede
tocar (A45).

Esto habilita experimentos acotados de verdad: acotar el radio de detección a un
foco conocido permite BAJAR umbrales sin inundarse de ruido, porque el área de
búsqueda cae con el cuadrado del radio (25 km → 1 km es 625× menos superficie).

Contrato que fijan estos tests:
  - sin `volcano_overrides` el comportamiento es idéntico al actual (nadie se
    entera de que esto existe);
  - el override es por NOMBRE de volcán y solo pisa las claves que nombra;
  - los volcanes no mencionados quedan intactos;
  - el override NO muta el YAML compartido en memoria (otro perfil que cargue
    después debe ver los valores originales).
"""
import copy

import pytest

import pipeline.profile as vrp_profile
from scripts.run_pipeline import apply_volcano_overrides


BASE = [
    {"name": "NevadosDeChillan", "lat": -36.863, "lon": -71.377,
     "vent_lat": -36.863, "vent_lon": -71.377,
     "radius_km": 25, "inner_radius_km": 5, "sensors": ["MODIS", "VIIRS"]},
    {"name": "Villarrica", "lat": -39.42, "lon": -71.93,
     "radius_km": 25, "inner_radius_km": 5},
]


def test_sin_overrides_no_cambia_nada(monkeypatch):
    monkeypatch.setattr(vrp_profile, "VOLCANO_OVERRIDES", {}, raising=False)
    original = copy.deepcopy(BASE)
    out = apply_volcano_overrides(copy.deepcopy(BASE))
    assert out == original


def test_override_pisa_solo_las_claves_nombradas(monkeypatch):
    monkeypatch.setattr(vrp_profile, "VOLCANO_OVERRIDES", {
        "NevadosDeChillan": {"vent_lat": -36.867210, "vent_lon": -71.378241,
                             "inner_radius_km": 1.0}}, raising=False)
    out = apply_volcano_overrides(copy.deepcopy(BASE))
    ndc = next(v for v in out if v["name"] == "NevadosDeChillan")
    assert ndc["vent_lat"] == pytest.approx(-36.867210)
    assert ndc["vent_lon"] == pytest.approx(-71.378241)
    assert ndc["inner_radius_km"] == 1.0
    # lo que el override NO nombra se conserva
    assert ndc["radius_km"] == 25, "radius_km sostiene el anillo de fondo: no debe tocarse solo"
    assert ndc["sensors"] == ["MODIS", "VIIRS"]


def test_volcanes_no_nombrados_quedan_intactos(monkeypatch):
    monkeypatch.setattr(vrp_profile, "VOLCANO_OVERRIDES", {
        "NevadosDeChillan": {"inner_radius_km": 1.0}}, raising=False)
    out = apply_volcano_overrides(copy.deepcopy(BASE))
    vil = next(v for v in out if v["name"] == "Villarrica")
    assert vil["inner_radius_km"] == 5


def test_override_de_volcan_inexistente_no_explota(monkeypatch):
    monkeypatch.setattr(vrp_profile, "VOLCANO_OVERRIDES", {
        "VolcanQueNoExiste": {"inner_radius_km": 1.0}}, raising=False)
    out = apply_volcano_overrides(copy.deepcopy(BASE))
    assert len(out) == 2


def test_no_muta_la_entrada_compartida(monkeypatch):
    """Otro perfil cargado después debe ver los valores originales."""
    monkeypatch.setattr(vrp_profile, "VOLCANO_OVERRIDES", {
        "NevadosDeChillan": {"inner_radius_km": 1.0}}, raising=False)
    entrada = copy.deepcopy(BASE)
    apply_volcano_overrides(entrada)
    ndc = next(v for v in entrada if v["name"] == "NevadosDeChillan")
    assert ndc["inner_radius_km"] == 5, "la lista de entrada no debe mutarse in-place"
