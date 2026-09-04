# -*- coding: utf-8 -*-
"""
S133 - Los short_name NRT de MODIS tienen que ser los que EXISTEN en el CMR.

FICHA SDA - no participa del calculo de la deteccion, pero decide QUE granules entran al
sistema. Un nombre de coleccion equivocado no produce un error: produce cero resultados,
y cero resultados es indistinguible de "todavia no hay dato".

EL FENOMENO. LANCE (el servicio casi-en-tiempo-real de NASA) publica los granules unas 3 h
despues de la pasada; el archivo Standard de LAADS tarda de horas a dias. Nuestro fetch
busca Standard primero y cae a NRT cuando Standard no esta. Esa caida es lo que nos permite
ver una anomalia la misma noche en vez de dos dias despues.

EL DEFECTO QUE ESTE TEST FIJA (S133). Para MODIS pediamos `MOD021KM_NRT` / `MYD021KM_NRT`
en version "61". **Esas colecciones no existen.** LANCE nombra sus colecciones de MODIS con
el mismo short_name del Standard y la version con sufijo: `MYD021KM` v`6.1NRT`. El sufijo
`_NRT` en el short_name SI es el esquema correcto para VIIRS (`VNP02IMG_NRT`), y de ahi
salio el error: se extrapolo el esquema de un sensor al otro (misma familia que A37).

Consecuencia medida el 2026-09-04: MIROVA publico una anomalia MODIS de 4,75 MW en
Villarrica de la pasada de las 07:50 UTC y nosotros no la teniamos. La busqueda con el
nombre que usabamos devolvia 0 granules; con el nombre real devuelve exactamente esa
pasada. Como el Standard de Aqua venia ademas 36 h atrasado, no habia por donde entrara.

Este test es OFFLINE a proposito: valida la FORMA de la tabla, no la red. Un test que
consulte el CMR fallaria por causas ajenas (red, mantenimiento de NASA) y se terminaria
ignorando, que es como mueren los guards.
"""
import re

import pytest

from pipeline.fetch import PRODUCTS

MODIS = [k for k in PRODUCTS if k.startswith("MODIS_")]
VIIRS = [k for k in PRODUCTS if k.startswith("VIIRS_")]


def _versiones(entrada):
    """La tabla admite `version` (str) o `versions` (lista). Devuelve siempre lista."""
    if "versions" in entrada:
        return list(entrada["versions"])
    return [entrada["version"]] if "version" in entrada else []


def test_la_tabla_declara_nrt_para_todos_los_modis():
    """Sin rama NRT no hay casi-tiempo-real posible, por muy bien nombrada que este."""
    sin_nrt = [k for k in MODIS if "nrt" not in PRODUCTS[k]]
    assert not sin_nrt, "productos MODIS sin fallback NRT: %s" % sin_nrt


@pytest.mark.parametrize("clave", MODIS)
def test_el_nrt_de_modis_no_usa_el_sufijo__NRT_en_el_short_name(clave):
    """
    LANCE no publica `MYD021KM_NRT`: publica `MYD021KM` en version 6.1NRT. Pedir el
    nombre con sufijo devuelve cero granules en silencio.
    """
    nrt = PRODUCTS[clave]["nrt"]
    assert not nrt["short_name"].endswith("_NRT"), (
        "%s pide '%s', que no existe en el CMR. Para MODIS el NRT va en la VERSION "
        "(6.1NRT), no en el short_name." % (clave, nrt["short_name"]))


@pytest.mark.parametrize("clave", MODIS)
def test_el_nrt_de_modis_comparte_short_name_con_el_standard(clave):
    """La coleccion NRT de LANCE es el MISMO producto, distinta version."""
    p = PRODUCTS[clave]
    assert p["nrt"]["short_name"] == p["short_name"], (
        "%s: NRT '%s' deberia ser el mismo short_name que el Standard '%s'"
        % (clave, p["nrt"]["short_name"], p["short_name"]))


@pytest.mark.parametrize("clave", MODIS)
def test_la_version_nrt_de_modis_lleva_el_sufijo_NRT(clave):
    """Forma exacta observada en el CMR: '6.1NRT' (tambien existe '6NRT', mas viejo)."""
    vs = _versiones(PRODUCTS[clave]["nrt"])
    assert vs, "%s: la rama NRT no declara version" % clave
    for v in vs:
        assert re.fullmatch(r"\d+(\.\d+)?NRT", v), (
            "%s: version NRT '%s' no tiene la forma <numero>NRT que usa LANCE para MODIS"
            % (clave, v))


@pytest.mark.parametrize("clave", VIIRS)
def test_el_nrt_de_viirs_conserva_el_sufijo__NRT(clave):
    """
    CONTROL, y es la mitad importante del test. El esquema de VIIRS es el OPUESTO y esta
    BIEN: `VNP02IMG_NRT` existe y devuelve datos. Sin este control, alguien podria
    "arreglar" VIIRS por simetria con MODIS y romper lo unico que funcionaba.
    """
    nrt = PRODUCTS[clave]["nrt"]
    assert nrt["short_name"].endswith("_NRT"), (
        "%s: VIIRS SI usa el sufijo _NRT en el short_name; no lo alinees con MODIS"
        % clave)
    for v in _versiones(nrt):
        assert "NRT" not in v, (
            "%s: en VIIRS el NRT va en el short_name, no en la version ('%s')"
            % (clave, v))


def test_los_dos_esquemas_conviven_y_esa_asimetria_es_deliberada():
    """
    Deja escrito, en forma ejecutable, que la diferencia entre sensores NO es un descuido.
    Es la leccion A37: el esquema de un sensor no se extrapola al otro.
    """
    modis_con_sufijo = [k for k in MODIS if PRODUCTS[k]["nrt"]["short_name"].endswith("_NRT")]
    viirs_sin_sufijo = [k for k in VIIRS
                        if not PRODUCTS[k]["nrt"]["short_name"].endswith("_NRT")]
    assert not modis_con_sufijo and not viirs_sin_sufijo, (
        "se mezclaron los esquemas: MODIS con _NRT=%s ; VIIRS sin _NRT=%s"
        % (modis_con_sufijo, viirs_sin_sufijo))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ────────────────────────────────────────────────────────────────────
# Segunda mitad del mismo defecto: detectar que un granule ES de NRT.
#
# POR QUE. `store.py` reemplaza por la calibracion definitiva SOLO los records marcados
# `nrt`. Un granule NRT etiquetado `standard` nunca se actualiza: se queda con la
# calibracion provisional para siempre, y en silencio.
#
# Los dos sensores marcan el NRT en el nombre de forma DISTINTA, verificado contra el
# CMR el 2026-09-04:
#     MODIS  MYD021KM.A2026247.0750.061.2026247092322.NRT.hdf   -> token ".NRT."
#     VIIRS  VNP02IMG_NRT.A2026247.0606.002.2026247081613.nc    -> prefijo "_NRT"
# El detector solo miraba "_NRT", asi que los NRT de MODIS pasaban por standard.
# ────────────────────────────────────────────────────────────────────

from pipeline.fetch import product_version_from_granule as _pv  # noqa: E402


@pytest.mark.parametrize("nombre", [
    "MYD021KM.A2026247.0750.061.2026247092322.NRT.hdf",   # el caso real de Villarrica
    "MOD021KM.A2026247.0215.061.2026247061218.NRT.hdf",
    "MYD03.A2026247.0750.061.2026247092322.NRT.hdf",
])
def test_los_granules_nrt_de_modis_se_reconocen_como_nrt(nombre):
    assert _pv(nombre) == "nrt", (
        "%s es de LANCE (token .NRT.) y se estaria guardando como 'standard'; "
        "store.py nunca lo reemplazaria por la calibracion definitiva" % nombre)


@pytest.mark.parametrize("nombre", [
    "VNP02IMG_NRT.A2026247.0606.002.2026247081613.nc",
    "VJ102IMG_NRT.A2026247.0554.021.2026247122413.nc",
])
def test_los_granules_nrt_de_viirs_se_siguen_reconociendo(nombre):
    """Control: la convencion que ya funcionaba no se rompe al agregar la otra."""
    assert _pv(nombre) == "nrt"


@pytest.mark.parametrize("nombre", [
    "MYD021KM.A2026247.0750.061.2026247092322.hdf",       # standard de verdad
    "MOD021KM.A2026001.0225.061.2026001131216.hdf",
    "VJ102IMG.A2026099.0554.021.2026099122413.nc",
    "VNP02IMG.A2026103.0554.002.2026103122413.nc",
])
def test_los_granules_estandar_no_se_marcan_como_nrt(nombre):
    """Que no haya falsos positivos: un standard marcado nrt se reprocesaria de mas."""
    assert _pv(nombre) == "standard"


def test_no_confunde_un_volcan_o_ruta_que_contenga_las_letras_nrt():
    """La marca es un token delimitado por puntos, no una subcadena suelta (A92)."""
    assert _pv("/datos/CONTRNRTO/MYD021KM.A2026247.0750.061.x.hdf") == "standard"
