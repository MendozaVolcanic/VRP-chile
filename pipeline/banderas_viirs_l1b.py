# FICHA (SDA, CPLT 372): lectura de radiancias del L1B de VIIRS, parte común de la vía «código MIROVA»
# (pipeline/mirova_v750_codigo.py::leer_radiancia_l1b) y de la guardia K (pipeline/process_viirs_mod.py::read_viirs_mod_l1b).
# Qué decide: qué DN crudo de una banda EV es una medición y cuál es una bandera (Missing_EV, Bowtie_Deleted, Cal_Fail)
# o relleno. No detecta ni clasifica; lo que marca como bandera llega a NaN antes de la detección.
"""Separar medición de bandera en el L1B de VIIRS con los atributos de cada variable.

POR QUÉ (S192). El UserGuide VIIRS L1B (Aug 2021, págs. 21 y 23) describe todas las radiancias EV como uint16, con el
rango válido hasta 65527 y las banderas 65532 a 65534 (relleno 65535). El archivo real de VJ202MOD_NRT v2.1 no lo
cumple en M13: viene en uint32, con valid_max 327670, banderas 327677 a 327679 y relleno 327680 (probe S192, run
44820394068, `D:\\vrp-trabajo\\temporales\\s192\\bowtie\\INFORME.md` §5). M13 es la banda de 4 µm que ve la lava: NASA
le dio más resolución sin cambiar su techo (530 W m-2 sr-1 um-1, unos 666 K). Un corte fijo en 65528 borraba en M13
todo píxel sobre unos 512 K, justo el del foco en una fase efusiva; y una lista fija {65532..65535} dejaba pasar las
banderas reales de M13 y borraba valores válidos. El archivo trae su propio `valid_max` por variable: es la regla.
Las banderas y el relleno quedan por encima de valid_max en las dos codificaciones (M13: 327677 a 327680 sobre 327670;
uint16: 65532 a 65535 sobre 65527), así que basta con «DN > valid_max».
"""
import numpy as np

# Respaldo para un archivo uint16 sin atributo valid_max (los L1B sintéticos de las pruebas; los de NASA lo traen):
# el máximo válido de las tablas de variables EV del UserGuide (págs. 21 y 23, «Max = 65527»).
VALID_MAX_UINT16_USERGUIDE = 65527


def dn_invalido(ds, dn):
    """Máscara (True = no es medición) del DN crudo `dn` leído del dataset `ds` de h5py.

    El corte es el `valid_max` de la variable. Sin ese atributo, un uint16 usa el del UserGuide; otro tipo no tiene base
    para separar medición de bandera y es un error: la pasada no se mide (sale como error_procesamiento) en vez de
    publicarse con un corte inventado."""
    vmax = ds.attrs.get("valid_max")
    if vmax is None:
        if np.dtype(ds.dtype) != np.uint16:
            raise ValueError(f"{ds.name}: {ds.dtype} sin valid_max; no hay base para separar medición de bandera")
        vmax = VALID_MAX_UINT16_USERGUIDE
    return np.asarray(dn) > np.asarray(vmax).ravel()[0]
