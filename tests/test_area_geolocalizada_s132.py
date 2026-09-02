# -*- coding: utf-8 -*-
"""S132 — área de píxel medida desde la geolocalización del granule (decisión #5).

EL FENÓMENO. Un sensor de barrido no mira siempre hacia abajo: cuando apunta de reojo al
borde del swath, el mismo detector cubre un pedazo de terreno mucho más grande que en el
nadir. La energía radiante que calculamos es una radiancia (por unidad de área) MULTIPLICADA
por el área del píxel, así que si el área que usamos es la del nadir mientras el píxel real
es el doble o el cuádruple, sub-reportamos la magnitud justo en las pasadas oblicuas.

S131 midió el efecto: en VIIRS la razón contra MIROVA cae de 0,77 en el nadir a 0,45 en el
bin de 50°+ si no se corrige, y queda plana entre 0,79 y 0,87 aplicando la ley de área del
ATBD. O sea, **el área explica el gradiente cenital completo**; lo que sobra después es un
déficit uniforme de ~0,82 que ya no es geometría.

POR QUÉ MEDIRLA Y NO MODELARLA. VIIRS no crece suave con el ángulo: hace agregación de
bow-tie a bordo (Wolfe et al. 2013), que junta 3, 2 o 1 muestras del detector según la zona
del swath, de modo que el área da SALTOS en dos fronteras en vez de seguir una curva. Todo
modelo analítico —el sec³ de un barredor puro, o el factor lineal capado a 2,0 que este
repo tenía— se equivoca en algún tramo: el propio docstring de `viirs_pixel_areas` reconoce
que su tope de 2,0× sub-corrige, porque el ATBD da 4,38× de nadir a borde de swath.

La geolocalización del granule, en cambio, no es un modelo: es dónde cayó cada píxel. La
distancia en el terreno entre centros vecinos ES el tamaño del píxel, con los saltos de
agregación ya incluidos, sin suponer nada sobre la órbita ni sobre el sensor.

Arranca APAGADO. Cambiar el área cambia la magnitud de todos los records y —lección A67 del
nadir-fijo— también puede cambiar la DETECCIÓN, porque el área multiplica dentro de la
integral de energía del Test 1. Se adopta por A/B con reproc real, no por flip.
"""
import numpy as np
import pytest

from pipeline.scan_geometry import pixel_areas_from_geolocation


def _grilla_regular(nfilas, ncols, lat0, lon0, paso_lat_km, paso_lon_km):
    """Grilla sintética con paso constante en el terreno, para tener área conocida."""
    dlat = paso_lat_km / 111.195
    lats = lat0 + dlat * np.arange(nfilas)[:, None] * np.ones((1, ncols))
    dlon = paso_lon_km / (111.195 * np.cos(np.radians(lat0)))
    lons = lon0 + dlon * np.ones((nfilas, 1)) * np.arange(ncols)[None, :]
    return lats, lons


def test_grilla_de_paso_conocido_da_el_area_esperada():
    """Control de instrumento: con paso de 0,375 km por lado el área debe dar 140.625 m²,
    que es exactamente el píxel nadir de I-band. Si esto falla, nada de lo demás vale."""
    lat, lon = _grilla_regular(9, 9, -39.42, -71.93, 0.375, 0.375)
    a = pixel_areas_from_geolocation(lat, lon)
    centro = a[4, 4]
    assert centro == pytest.approx(140625.0, rel=0.01), f"{centro:.0f} m²"


def test_el_area_crece_cuando_crece_el_paso():
    """Es la propiedad física que justifica todo: píxel oblicuo = píxel más grande."""
    lat_n, lon_n = _grilla_regular(9, 9, -39.42, -71.93, 0.375, 0.375)
    lat_b, lon_b = _grilla_regular(9, 9, -39.42, -71.93, 0.375, 0.800)
    a_nadir = pixel_areas_from_geolocation(lat_n, lon_n)[4, 4]
    a_borde = pixel_areas_from_geolocation(lat_b, lon_b)[4, 4]
    assert a_borde / a_nadir == pytest.approx(0.800 / 0.375, rel=0.02)


def test_captura_un_salto_de_agregacion_sin_suavizarlo():
    """La razón de medir en vez de modelar: el bow-tie da SALTOS, no una curva.
    Una grilla con el paso duplicado a partir de cierta columna debe mostrar el salto."""
    lat, lon = _grilla_regular(7, 12, -39.42, -71.93, 0.375, 0.375)
    dlon = (lon[0, 1] - lon[0, 0])
    for j in range(7, 12):                      # a partir de la columna 7, paso doble
        lon[:, j] = lon[:, 6] + 2 * dlon * (j - 6)
    a = pixel_areas_from_geolocation(lat, lon)
    assert a[3, 9] / a[3, 3] == pytest.approx(2.0, rel=0.05)


def test_los_bordes_no_quedan_en_nan():
    """Un NaN en el borde del granule propagaría a la magnitud de esos píxeles."""
    lat, lon = _grilla_regular(6, 6, -39.42, -71.93, 0.375, 0.375)
    a = pixel_areas_from_geolocation(lat, lon)
    assert np.isfinite(a).all()
    assert a.shape == lat.shape


def test_geolocalizacion_invalida_devuelve_nan_no_un_numero_inventado():
    """Si la geolocalización viene corrupta es mejor un NaN visible que un área plausible
    pero falsa, que se propagaría a la magnitud sin que nadie lo note."""
    lat, lon = _grilla_regular(6, 6, -39.42, -71.93, 0.375, 0.375)
    lat[2, 2] = np.nan
    a = pixel_areas_from_geolocation(lat, lon)
    assert np.isnan(a[2, 2])
    assert np.isfinite(a[0, 0])


def test_el_flag_arranca_apagado():
    from pipeline.profile import ENABLE_GEOLOCATED_PIXEL_AREA
    assert ENABLE_GEOLOCATED_PIXEL_AREA is False


def test_reproduce_la_razon_del_atbd_viirs():
    """Control contra autoridad externa, no contra mis propias grillas.

    El ATBD de geolocalización VIIRS (423-ATBD-002, Tabla 2.2-1) da el tamaño en el terreno
    del píxel I4: 0,371 × 0,388 km en el nadir y 0,80 × 0,789 km al final del swath. Eso es
    0,144 → 0,631 km², **4,38×** — el número que S131 usó para mostrar que el tope de 2,0×
    del modelo lineal del repo sub-corrige a menos de la mitad.

    Si se le dan a la función esos dos pasos, tiene que devolver esa razón. Es la prueba de
    que mide lo que dice medir, y no una construcción interna que se confirma sola.
    """
    lat_n, lon_n = _grilla_regular(9, 9, 0.0, 0.0, 0.388, 0.371)   # nadir: track × scan
    lat_b, lon_b = _grilla_regular(9, 9, 0.0, 0.0, 0.789, 0.800)   # borde de swath
    a_n = pixel_areas_from_geolocation(lat_n, lon_n)[4, 4]
    a_b = pixel_areas_from_geolocation(lat_b, lon_b)[4, 4]

    assert a_n / 1e6 == pytest.approx(0.144, abs=0.005), f"nadir {a_n/1e6:.4f} km²"
    assert a_b / 1e6 == pytest.approx(0.631, abs=0.010), f"borde {a_b/1e6:.4f} km²"
    assert a_b / a_n == pytest.approx(4.38, rel=0.02)


def test_el_modelo_lineal_del_repo_subcorrige_frente_a_lo_medido():
    """Deja escrito por qué el frente existe: el modelo vigente tapa a 2,0× un efecto de
    4,38×, o sea corrige menos de la mitad de lo que hay que corregir."""
    from pipeline.scan_geometry import MAX_SENSOR_ZENITH_DEG, viirs_pixel_areas
    # El máximo que el modelo puede dar: su tope declarado es 2,0 pero nunca llega a morder,
    # porque el zenith se clipea antes en MAX_SENSOR_ZENITH_DEG = 70°, donde el factor vale
    # 1,96. (Lo verifiqué al escribir este test: había asumido que el tope de 2,0 mandaba.)
    peor = viirs_pixel_areas(np.array([MAX_SENSOR_ZENITH_DEG]), 140625.0,
                             nadir_fixed=False)[0] / 140625.0
    assert peor == pytest.approx(1.96, abs=0.01), f"el modelo lineal cambió: {peor:.3f}"
    # Contra los 4,38× que el ATBD mide, el modelo corrige menos de la mitad.
    assert peor < 4.38 / 2, f"{peor:.2f} vs mitad de 4,38"
