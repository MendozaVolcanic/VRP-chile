"""S103 — Integration guard: el flag nadir-fijo cambia el AREA que cada
procesador usa para calcular el VRP (cierra el gap A45 de la auditoria
docs/AUDIT_S103_PRE_VIIRS.md).

Motivacion fisica
-----------------
MIROVA resamplea cada granule a una grid de area constante (Coppola 2016a
SP426.5 Eq.7): NO usa el area real off-nadir, que crece con el angulo de
barrido (sec^3 en MODIS; factor lineal aggregado en VIIRS). Si dejamos el
area off-nadir activa, el VRP de los pixeles lejanos del nadir se infla. El
flag ``enable_nadir_fixed_pixel_area_{modis,viirs}`` restaura el clon literal
fijando el area al valor nadir.

Por que existe este test
------------------------
``test_drift7_nadir_fixed_pixel.py`` prueba que ``modis_pixel_areas`` /
``viirs_pixel_areas`` devuelven el area correcta segun el flag, AISLADAS.
``test_gr2_profile_invariants.py`` pinea el VALOR del flag en el perfil
operacional. Lo que faltaba (gap A45, el mismo que MODIS arrastraba hasta
S102) es el eslabon del medio: que ``calculate_vrp`` de cada procesador
(1) derive ``pixel_areas`` DEL flag nadir y (2) calcule el VRP a partir de
ese ``pixel_areas`` con la formula Wooster ``VRP = A_pix * k * dL``. Si ese
cableado se rompe (alguien hardcodea el area, o desconecta el flag), el flag
queda MUERTO: un reproc "nadir" no cambiaria la magnitud. Eso es exactamente
lo que un test debe atrapar ANTES de adoptar nadir VIIRS (A45).

Offline puro: corre las funciones de area con datos sinteticos + inspecciona
el fuente de ``calculate_vrp``. NO corre el pipeline (sin L1B/GEO), igual que
el resto de los guards de procesador (test_gr1, test_viirs_path_d).
"""
import inspect
import re

import numpy as np
import pytest

import pipeline.process_modis as p_modis
import pipeline.process_viirs as p_viirs_i      # VIIRS I-band 375 m
import pipeline.process_viirs_mod as p_viirs_m  # VIIRS M-band 750 m
from pipeline.scan_geometry import modis_pixel_areas, viirs_pixel_areas


OFF_NADIR_ZEN_DEG = 60.0  # pixel claramente fuera del nadir (cos=0.5)


# --------------------------------------------------------------------------
# (1) Comportamiento: el flag REDUCE el area de un pixel off-nadir al area
# nadir uniforme. Usa las funciones y constantes REALES de cada modulo.
# --------------------------------------------------------------------------
def test_nadir_flag_reduces_offnadir_area_viirs_iband():
    a_off = viirs_pixel_areas(
        np.array([OFF_NADIR_ZEN_DEG]), p_viirs_i.NADIR_PIXEL_AREA_M2, nadir_fixed=False)[0]
    a_nad = viirs_pixel_areas(
        np.array([OFF_NADIR_ZEN_DEG]), p_viirs_i.NADIR_PIXEL_AREA_M2, nadir_fixed=True)[0]
    assert a_nad == p_viirs_i.NADIR_PIXEL_AREA_M2  # 140625 m^2 uniforme
    assert a_off > a_nad  # off-nadir inflado por el factor lineal aggregado


def test_nadir_flag_reduces_offnadir_area_viirs_mband():
    a_off = viirs_pixel_areas(
        np.array([OFF_NADIR_ZEN_DEG]), p_viirs_m.NADIR_PIXEL_AREA_M2, nadir_fixed=False)[0]
    a_nad = viirs_pixel_areas(
        np.array([OFF_NADIR_ZEN_DEG]), p_viirs_m.NADIR_PIXEL_AREA_M2, nadir_fixed=True)[0]
    assert a_nad == p_viirs_m.NADIR_PIXEL_AREA_M2  # 562500 m^2 uniforme
    assert a_off > a_nad


def test_nadir_flag_reduces_offnadir_area_modis():
    shape = (1, 1354)  # swath MODIS; col 0 = borde (maximo off-nadir)
    a_off = modis_pixel_areas(shape, nadir_fixed=False)[0, 0]
    a_nad = modis_pixel_areas(shape, nadir_fixed=True)[0, 0]
    assert a_nad == p_modis.NADIR_PIXEL_AREA_M2  # 1e6 uniforme
    assert a_off > 4 * a_nad  # sec^3 en el borde >> nadir


# --------------------------------------------------------------------------
# (2) Consecuencia en el VRP: como VRP = A_pix * WOOSTER_COEFF * dL, fijar el
# area nadir reduce el VRP de un pixel off-nadir por EXACTAMENTE el ratio de
# areas. Usa la funcion de area real + el WOOSTER_COEFF real de cada modulo
# (la formula se valida contra el fuente en (3)).
# --------------------------------------------------------------------------
def _vrp_mw(area_m2, wooster_k, delta_L=1.0):
    return area_m2 * wooster_k * delta_L / 1e6


@pytest.mark.parametrize("mod", [p_viirs_i, p_viirs_m], ids=["iband", "mband"])
def test_vrp_scales_with_area_when_nadir_flips_viirs(mod):
    a_off = viirs_pixel_areas(
        np.array([OFF_NADIR_ZEN_DEG]), mod.NADIR_PIXEL_AREA_M2, nadir_fixed=False)[0]
    a_nad = viirs_pixel_areas(
        np.array([OFF_NADIR_ZEN_DEG]), mod.NADIR_PIXEL_AREA_M2, nadir_fixed=True)[0]
    vrp_off = _vrp_mw(a_off, mod.WOOSTER_COEFF)
    vrp_nad = _vrp_mw(a_nad, mod.WOOSTER_COEFF)
    assert vrp_nad < vrp_off  # nadir desinfla la magnitud off-nadir
    assert np.isclose(vrp_nad / vrp_off, a_nad / a_off)  # exacto: VRP propto area


def test_vrp_scales_with_area_when_nadir_flips_modis():
    shape = (1, 1354)
    a_off = modis_pixel_areas(shape, nadir_fixed=False)[0, 0]
    a_nad = modis_pixel_areas(shape, nadir_fixed=True)[0, 0]
    vrp_off = _vrp_mw(a_off, p_modis.WOOSTER_COEFF)
    vrp_nad = _vrp_mw(a_nad, p_modis.WOOSTER_COEFF)
    assert vrp_nad < vrp_off
    assert np.isclose(vrp_nad / vrp_off, a_nad / a_off)


# --------------------------------------------------------------------------
# (3) Cableado (EL gap A45): cada calculate_vrp deriva pixel_areas DEL flag
# nadir Y calcula el VRP a partir de ese pixel_areas con WOOSTER_COEFF. Si
# alguien hardcodea el area o desconecta el flag, el flag queda muerto y esto
# falla (tripwire — actualizar deliberadamente si se refactoriza el seam).
# --------------------------------------------------------------------------
# (modulo, funcion de area esperada, constante de flag del modulo)
#
# S133: en VIIRS la funcion pasó a ser `resolve_viirs_pixel_areas`, que elige entre los
# tres modos de area (geolocalizado / nadir-fijo / factor lineal) y sigue recibiendo el
# flag nadir. La actualizacion es deliberada, que es lo que el comentario de arriba pide
# al refactorizar el seam.
#
# ⚠️ Y hubo que endurecer la comprobacion. `viirs_pixel_areas` es SUBCADENA de
# `resolve_viirs_pixel_areas`, asi que la version anterior de este test seguia en verde
# despues de que la llamada directa desaparecio: pasaba por coincidencia de texto, no
# porque el cableado siguiera ahi. Un guard que pasa por la razon equivocada es peor que
# no tenerlo, porque da permiso. Ahora se exige la llamada con frontera de palabra.
WIRING = [
    (p_viirs_i, "resolve_viirs_pixel_areas", "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS"),
    (p_viirs_m, "resolve_viirs_pixel_areas", "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS"),
    (p_modis,   "modis_pixel_areas", "ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS"),
]


@pytest.mark.parametrize(
    "mod,area_fn,flag", WIRING, ids=[m[0].__name__ for m in WIRING])
def test_calculate_vrp_derives_pixel_areas_from_nadir_flag(mod, area_fn, flag):
    src = inspect.getsource(mod.calculate_vrp)
    src_nospace = re.sub(r"\s", "", src)
    # (a) pixel_areas se computa con la funcion de area pasando el flag nadir.
    # Frontera de palabra a la izquierda: `resolve_viirs_pixel_areas(` NO puede satisfacer
    # una expectativa de `viirs_pixel_areas(` ni al reves.
    assert re.search(r"(?<![A-Za-z0-9_])" + re.escape(area_fn) + r"\s*\(", src), (
        f"{mod.__name__}.calculate_vrp no llama {area_fn}() "
        f"(ojo: una subcadena de otro nombre no cuenta)"
    )
    assert "nadir_fixed=" + flag in src_nospace, (
        f"{mod.__name__}.calculate_vrp no pasa nadir_fixed={flag} a {area_fn} "
        f"-> el flag nadir quedaria muerto (gap A45)"
    )
    # (b) el VRP (Wooster) y el pixel_areas flageado viven en la misma funcion:
    # el area por-pixel se indexa de pixel_areas y se multiplica por WOOSTER_COEFF.
    # S133: frontera de palabra. `pixel_areas` es subcadena de los cuatro nombres de
    # funcion de area del modulo, asi que un `in` pelado se satisface con la llamada sola
    # y no prueba que el array llegue a usarse.
    assert re.search(r"(?<![A-Za-z0-9_])pixel_areas(?![A-Za-z0-9_])", src), (
        f"{mod.__name__}.calculate_vrp no usa la variable pixel_areas")
    assert "WOOSTER_COEFF" in src, (
        f"{mod.__name__}.calculate_vrp no calcula VRP con WOOSTER_COEFF "
        f"-> no se puede garantizar que el area flageada llegue al VRP"
    )


@pytest.mark.parametrize(
    "mod,flag", [(p_modis, "ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS"),
                 (p_viirs_i, "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS"),
                 (p_viirs_m, "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS")],
    ids=["modis", "iband", "mband"])
def test_nadir_flag_constant_reaches_each_module(mod, flag):
    """El flag llega como constante de modulo (desde pipeline.profile), no es
    un nombre suelto en el call site. Sin esto, getsource podria pasar pero el
    import romperia en runtime."""
    assert hasattr(mod, flag), f"{mod.__name__} no expone {flag} desde profile"
    assert isinstance(getattr(mod, flag), bool)
