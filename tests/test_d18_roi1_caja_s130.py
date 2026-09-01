"""D18 (S130) — el ROI1 del paper es una CAJA de 5x5 km, no un circulo per-volcan.

POR QUE EXISTE
--------------
Coppola 2016a SP426.5, verbatim:

    "the inner region (ROI1) consists of a box (5 x 5 km) centred on the
     volcano's summit"

Una caja de 25 km2, IGUAL PARA TODOS. Lo nuestro es un circulo de radio
`inner_radius_km` que va de 3 km (Lastarria, Planchon-Peteroa) a 20 km (PCC).

El ROI1 decide que umbrales rigen: adentro N.sigma = 5 y C1 = 0,003 (sensible),
afuera 10 y 0,010 (estricto). Agrandarlo afloja el umbral sobre mas terreno.

Medido antes de implementar (experiments/_s129_roi1/): de los 107.585 pixeles que
hoy reciben el trato de summit, solo 33.437 caerian dentro de la caja del paper —
el 68,9 % lo recibe por una geometria que el canon no respalda. En detecciones, el
42 % de las summit tienen su cluster fuera de la caja, y se concentran en los
nevados de senal debil (Llaima 71,6 % · Copahue 69,5 % · Villarrica 66,4 %) que es
justo donde vive el sesgo topografico A69 — pero tambien donde vive cat-b real
(Lastarria/Lazufre, PCC/lacolito).

Hay precedente: S15 Tema E ya cambio el ROI EXTERIOR de circulo a caja por paridad
MIROVA (`roi_mask_bbox`, scan_geometry.py:150). Esto es el mismo cambio para el ROI
interior, reusando esa funcion con half_km = 2,5.

ENTRA EN OFF. El flag `enable_roi1_box_paper` es False por default y en el perfil
operacional: la direccion del cambio es MENOS detecciones, y `mirova_equivalent`
prioriza recall sobre precision — adoptarlo es decision de mision, no tecnica. Estos
tests cubren el mecanismo para que el A/B pueda correrse sobre algo verificado.
"""
import numpy as np
import pytest

from pipeline.detection_context import roi1_summit_mask
from pipeline.scan_geometry import roi_mask_bbox


def _grilla(n=41, span_deg=0.5, center=(-39.42, -71.94)):
    """Grilla lat/lon centrada en el vent, mas la distancia por pixel."""
    lat0, lon0 = center
    lats = np.linspace(lat0 - span_deg, lat0 + span_deg, n)
    lons = np.linspace(lon0 - span_deg, lon0 + span_deg, n)
    lon, lat = np.meshgrid(lons, lats)
    dlat_km = (lat - lat0) * 111.0
    dlon_km = (lon - lon0) * 111.0 * np.cos(np.radians(lat0))
    dist_km = np.sqrt(dlat_km ** 2 + dlon_km ** 2)
    return lat, lon, dist_km


def test_sin_mascara_es_el_circulo_de_siempre():
    """Sin roi1_mask el comportamiento es identico al `dist_km <= inner_km` previo.

    Es la garantia de retrocompatibilidad: con el flag OFF nada cambia.
    """
    _lat, _lon, dist = _grilla()
    got = roi1_summit_mask(dist, inner_km=5.0, roi1_mask=None)
    np.testing.assert_array_equal(got, dist <= 5.0)


def test_con_mascara_manda_la_mascara():
    """Con roi1_mask, la geometria la define la mascara y el radio se ignora."""
    _lat, _lon, dist = _grilla()
    caja = np.zeros_like(dist, dtype=bool)
    caja[10:15, 10:15] = True
    got = roi1_summit_mask(dist, inner_km=20.0, roi1_mask=caja)
    np.testing.assert_array_equal(got, caja)
    # el radio de 20 km habria marcado muchisimo mas
    assert (dist <= 20.0).sum() > caja.sum()


def test_la_caja_del_paper_es_mas_chica_que_el_circulo_de_5km():
    """La caja 5x5 (25 km2) contra el circulo r=5 km (78,5 km2): 3,1x menos area.

    Es el numero de D18 para los seis volcanes con inner = 5 km.
    """
    lat, lon, dist = _grilla()
    caja = roi_mask_bbox(lat, lon, -39.42, -71.94, half_km=2.5)
    circulo = dist <= 5.0
    assert caja.sum() < circulo.sum()
    # la caja del paper cabe entera dentro del circulo de 5 km: su punto mas
    # lejano es la esquina, a 2,5*raiz(2) = 3,54 km < 5
    assert np.all(dist[caja] <= 2.5 * np.sqrt(2) + 0.2)


def test_la_caja_conserva_las_esquinas_que_un_circulo_de_igual_area_pierde():
    """La FORMA importa: el paper dice caja, no circulo de area equivalente.

    Un circulo de 25 km2 tiene radio 2,82 km. La esquina de la caja esta a 3,54 km,
    asi que hay pixeles que la caja incluye y ese circulo no. Por eso el brazo fiel
    del A/B tiene que ser una CAJA y no un circulo de radio ajustado.
    """
    lat, lon, dist = _grilla(n=121, span_deg=0.1)
    caja = roi_mask_bbox(lat, lon, -39.42, -71.94, half_km=2.5)
    circulo_igual_area = dist <= np.sqrt(25.0 / np.pi)
    solo_caja = caja & ~circulo_igual_area
    assert solo_caja.sum() > 0, "las esquinas de la caja deben aportar pixeles"


def test_el_flag_operacional_esta_en_off():
    """D18 NO se adopta sin decision de mision: la direccion es menos detecciones."""
    import importlib
    import os
    prev = os.environ.get("VRP_PROFILE")
    os.environ["VRP_PROFILE"] = "mirova_equivalent"
    import pipeline.profile as p
    importlib.reload(p)
    try:
        assert p.ENABLE_ROI1_BOX_PAPER is False, (
            "enable_roi1_box_paper debe seguir en False en el perfil operacional: "
            "corregir la geometria del ROI1 da MENOS detecciones y mirova_equivalent "
            "prioriza recall. Encenderlo requiere el A/B y decision de Nicolas."
        )
        assert p.ROI1_BOX_HALF_KM == 2.5, "la caja del paper es 5x5 km -> semilado 2,5"
    finally:
        if prev is None:
            os.environ.pop("VRP_PROFILE", None)
        else:
            os.environ["VRP_PROFILE"] = prev
        importlib.reload(p)


# ── Control de instrumento: que el flag ON cambie el RESULTADO, no solo exista ──
# Leccion de S130 (feedback_s130_medir_el_sustrato_antes_del_ab): el A/B de los
# fondos gasto mas de cinco horas de CI para descubrir que sus flags no producian
# efecto. Antes de correr el A/B de D18, estos dos tests comprueban que la caja
# LLEGA a las funciones de deteccion y cambia lo que declaran anomalo.

def test_la_caja_cambia_lo_que_el_umbral_BT_declara_anomalo():
    """dual_roi_bt_threshold con la caja marca MENOS que con el circulo.

    Es el mecanismo de D18: un pixel tibio a 4 km del crater recibe hoy el umbral
    laxo de summit (N.sigma = 5) porque cae dentro del circulo de 5 km; con la caja
    del paper pasa a scene (N.sigma = 10) y deja de pasar.
    """
    from pipeline.detection_context import dual_roi_bt_threshold

    lat, lon, dist = _grilla(n=81, span_deg=0.09)
    roi = np.ones_like(dist, dtype=bool)
    t_bg, std_bg = 270.0, 1.0
    # campo tibio uniforme: 7 K sobre el fondo. Pasa 5.sigma (summit), no 10.sigma.
    bt = np.full_like(dist, t_bg + 7.0)

    comun = dict(bt=bt, roi_mask=roi, dist_km=dist, t_bg=t_bg, std_bg=std_bg,
                 inner_km=5.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
                 anomaly_floor_k=0.0, max_sigma_cap_k=999.0)

    circulo = dual_roi_bt_threshold(**comun)
    caja = dual_roi_bt_threshold(
        **comun, roi1_mask=roi_mask_bbox(lat, lon, -39.42, -71.94, half_km=2.5))

    assert circulo.sum() > caja.sum(), (
        "la caja del paper debe marcar menos que el circulo de 5 km: si no, el "
        "flag no esta llegando a la funcion de deteccion"
    )
    # y lo que sobrevive es lo que cae dentro de la caja
    assert caja.sum() > 0, "la caja no puede quedar vacia en este campo uniforme"


def test_los_tres_procesadores_construyen_la_caja_cuando_el_flag_esta_ON():
    """El cableado existe en los tres sensores, no solo en uno.

    Verifica el codigo fuente porque correr los tres procesadores necesita
    granules L1B reales (y pyhdf, que en Windows no corre — MODIS solo anda en
    Actions). Chequea las dos mitades del cableado: que se arme `_roi1_mask` bajo
    el flag y que se pase a las llamadas.
    """
    import os
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for f in ("process_modis.py", "process_viirs.py", "process_viirs_mod.py"):
        src = open(os.path.join(raiz, "pipeline", f), encoding="utf-8").read()
        assert "if ENABLE_ROI1_BOX_PAPER" in src, f"{f}: no arma la caja bajo el flag"
        assert "ROI1_BOX_HALF_KM)" in src, f"{f}: no usa el semilado configurable"
        n = src.count("roi1_mask=_roi1_mask")
        assert n == 5, f"{f}: esperaba 5 call sites con roi1_mask, hay {n}"
