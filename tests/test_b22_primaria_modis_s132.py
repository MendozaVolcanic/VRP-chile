# -*- coding: utf-8 -*-
"""S132 — B22 como banda MIR primaria en MODIS (decisión #6 de AUDIT_S131 §4).

POR QUÉ FÍSICO. Las bandas 21 y 22 de MODIS miran la MISMA ventana espectral (3,929-3,989
µm); lo que las separa es la ganancia. B21 es la de rango alto: aguanta hasta ~500 K sin
saturar, pero su ruido equivalente en temperatura es de 0,183 K. B22 es la de precisión:
satura a ~331 K, pero su ruido es de 0,017 K — un orden de magnitud más silenciosa. Para
una señal sub-píxel débil (el lago de lava de Villarrica, 0,05-0,2 MW) el ruido del fondo
es exactamente lo que decide si el píxel pasa el umbral contextual N·σ o no: medir el
fondo con la banda ruidosa infla σ y esconde la anomalía real.

QUÉ DICE EL PAPER. Coppola 2016a SP426.5 l.141-144, textual:

    "we built a corrected spectral band centred at 3.959 µm (hereby called band L21ok),
     by using the L21 or L22 radiance, depending on band 22 saturation (or not),
     respectively."

O sea: B22 manda, y B21 entra SÓLO cuando B22 saturó. El pipeline hacía lo contrario
(B21 primaria, B22 de respaldo) — es un drift no documentado respecto del clon literal.

POR QUÉ TRAS FLAG. El cambio no es cosmético ni sólo de magnitud: al bajar el ruido del
fondo se mueven los umbrales contextuales, así que mueve también la DETECCIÓN (es la
lección A67 del nadir-fijo). Se adopta por A/B con reproc real, no por flip a ciegas.

SEGURIDAD DE LA CAÍDA. `read_modis_granule.calibrate()` pone NaN en todo DN > 32767, que
cubre el sentinel 65533 "Detector is saturated" del MODIS L1B C7 UserGuide Tabla 5.6.1.
Es decir: la saturación de B22 SÍ llega marcada como NaN, que es la condición que la
regla del paper necesita para poder caer a B21. Sin eso el swap sub-reportaría en caliente.
"""
import numpy as np

from pipeline.process_modis import merge_mir_bands

NAN = np.nan


def test_flag_off_conserva_el_comportamiento_historico():
    """Control: apagado, B21 manda y B22 sólo tapa los NaN de B21."""
    rad21 = np.array([1.0, NAN, 3.0], dtype=np.float32)
    rad22 = np.array([9.0, 8.0, NAN], dtype=np.float32)
    out = merge_mir_bands(rad21, rad22, b22_primary=False)
    assert out[0] == 1.0      # B21 válido: gana B21
    assert out[1] == 8.0      # B21 NaN: cae a B22
    assert out[2] == 3.0      # B22 NaN: se queda con B21


def test_flag_on_b22_manda_cuando_no_saturo():
    """Coppola 2016a l.141-144: con B22 no saturada, la radiancia es la de B22."""
    rad21 = np.array([1.0, 2.0], dtype=np.float32)
    rad22 = np.array([9.0, 8.0], dtype=np.float32)
    out = merge_mir_bands(rad21, rad22, b22_primary=True)
    assert out[0] == 9.0
    assert out[1] == 8.0


def test_flag_on_cae_a_b21_donde_b22_saturo():
    """La saturación de B22 llega como NaN desde calibrate(); ahí y sólo ahí entra B21."""
    rad21 = np.array([1.0, 2.0], dtype=np.float32)
    rad22 = np.array([NAN, 8.0], dtype=np.float32)
    out = merge_mir_bands(rad21, rad22, b22_primary=True)
    assert out[0] == 1.0
    assert out[1] == 8.0


def test_ambas_invalidas_queda_nan_en_los_dos_modos():
    rad21 = np.array([NAN], dtype=np.float32)
    rad22 = np.array([NAN], dtype=np.float32)
    assert np.isnan(merge_mir_bands(rad21, rad22, b22_primary=False)[0])
    assert np.isnan(merge_mir_bands(rad21, rad22, b22_primary=True)[0])


def test_no_muta_las_bandas_de_entrada():
    """El merge es una lectura: los arrays crudos no se tocan (Data Integrity)."""
    rad21 = np.array([1.0, NAN], dtype=np.float32)
    rad22 = np.array([NAN, 8.0], dtype=np.float32)
    merge_mir_bands(rad21, rad22, b22_primary=True)
    assert rad21[0] == 1.0 and np.isnan(rad21[1])
    assert np.isnan(rad22[0]) and rad22[1] == 8.0


def test_flag_operacional_arranca_apagado():
    """Adopción por A/B (A67): el default del perfil operacional no cambia hoy."""
    from pipeline.profile import ENABLE_MODIS_B22_PRIMARY
    assert ENABLE_MODIS_B22_PRIMARY is False
