"""Tests del ROI cuadrado bbox (paridad geometrica MIROVA S15).

MIROVA usa bbox 50x50 km centrado en el vent (confirmado via KMZ
GroundOverlay LatLonBox en analisis S15). Nuestro pipeline usaba
circulo inscrito radio 25 km. Resultado: perdiamos 27% del area
MIROVA (las esquinas del bbox a 25-35 km diagonal del centro).

Este test valida la nueva funcion que genera roi_mask bbox en vez
de circular.
"""
import numpy as np
from pipeline.scan_geometry import roi_mask_bbox


def test_center_pixel_always_inside():
    """Pixel exacto en el centro debe estar dentro del ROI."""
    lat = np.array([[-38.692]])
    lon = np.array([[-71.729]])
    mask = roi_mask_bbox(lat, lon, -38.692, -71.729, 25.0)
    assert mask[0, 0] == True


def test_pixel_at_corner_of_bbox_included():
    """Pixel cerca de la esquina NE (24 km N, 24 km E) debe estar
    incluido en bbox 25 pero FUERA de un circulo de 25 km. Esta es la
    ganancia esperada del bbox sobre circulo inscrito."""
    lat_off = 24.0 / 111.0
    lon_off = 24.0 / (111.0 * np.cos(np.radians(-38.692)))
    lat = np.array([[-38.692 + lat_off]])
    lon = np.array([[-71.729 + lon_off]])
    mask = roi_mask_bbox(lat, lon, -38.692, -71.729, 25.0)
    # Distancia haversine desde centro es sqrt(24^2 + 24^2) ~ 33.9 km
    # -> fuera del circulo 25, dentro del bbox 25.
    assert mask[0, 0] == True


def test_pixel_outside_bbox_excluded():
    """Pixel a 30 km norte puro debe estar fuera."""
    lat_off = 30.0 / 111.0
    lat = np.array([[-38.692 + lat_off]])
    lon = np.array([[-71.729]])
    mask = roi_mask_bbox(lat, lon, -38.692, -71.729, 25.0)
    assert mask[0, 0] == False


def test_vectorized_shape_preserved():
    """Input 2D array devuelve mask 2D mismo shape."""
    lat = np.array([[-38.6, -38.7], [-38.5, -38.8]])
    lon = np.array([[-71.6, -71.7], [-71.5, -71.8]])
    mask = roi_mask_bbox(lat, lon, -38.7, -71.7, 25.0)
    assert mask.shape == (2, 2)


def test_llaima_conguillio_included_with_bbox():
    """Escenario real: Llaima -38.692, -71.729 con Conguillio lake
    aprox -38.65, -71.55 (a ~20 km NE). Con bbox 25 km debe ser TRUE,
    aunque la distancia haversine es ~22 km.

    Conguillio segun OSF/CSV esta a ~28 km (coordenadas del lake
    propio), dentro del bbox de 25 km pero fuera del circulo de 25 km.
    """
    # Punto a 20 km N, 15 km E del Llaima vent
    lat = np.array([[-38.692 + 20.0/111.0]])
    lon = np.array([[-71.729 + 15.0/(111.0*np.cos(np.radians(-38.692)))]])
    mask = roi_mask_bbox(lat, lon, -38.692, -71.729, 25.0)
    assert mask[0, 0] == True
