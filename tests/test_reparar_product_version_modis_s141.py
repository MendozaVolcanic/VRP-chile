# -*- coding: utf-8 -*-
"""S141: el re-etiquetado de records MODIS NRT decide por el nombre del granule guardado.

POR QUÉ: hasta #659 (S140) los tres procesadores escribían `"nrt" if "_NRT" in nombre`, y MODIS
marca sus granules NRT con `.NRT.`: al 14-sep había 254 records MODIS con granule `.NRT.`
etiquetados "standard" en los 11 Tier A. `store.py` sólo reemplaza por la calibración definitiva
los records "nrt", así que esos records se quedan con la calibración provisional para siempre.

El script de S133 preguntaba al CMR si existía el granule estándar y, si existía, NO re-etiquetaba.
Eso es justo al revés para los records que ya guardan su granule: si el nombre dice `.NRT.`, el
record se calculó con el producto NRT aunque hoy exista el estándar, y precisamente por eso debe
quedar "nrt" para que el upgrade de `store.py` lo reemplace. El nombre guardado es la prueba; el
CMR sólo sirve cuando el record no guarda el nombre.
"""
from scripts.reparar_product_version_modis_s133 import decidir_por_granule


def test_granule_nrt_de_modis_se_reetiqueta():
    r = {"sensor": "MODIS_AQUA", "product_version": "standard",
         "granule": "MYD021KM.A2026257.0735.061.2026257092822.NRT.hdf"}
    assert decidir_por_granule(r) == "nrt"


def test_granule_estandar_se_confirma():
    r = {"sensor": "MODIS_TERRA", "product_version": "standard",
         "granule": "MOD021KM.A2026114.0700.061.2026114191722.hdf"}
    assert decidir_por_granule(r) == "standard"


def test_sin_granule_no_se_decide_por_nombre():
    """Sin nombre guardado no hay prueba: queda para la consulta al CMR (camino S133)."""
    assert decidir_por_granule({"sensor": "MODIS_AQUA", "product_version": "standard"}) is None
    assert decidir_por_granule({"sensor": "MODIS_AQUA", "granule": ""}) is None


def test_granule_con_ruta_se_lee_por_el_nombre():
    r = {"granule": "/tmp/Lascar/MYD021KM.A2026257.0735.061.2026257092822.NRT.hdf"}
    assert decidir_por_granule(r) == "nrt"
