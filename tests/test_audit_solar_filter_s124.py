# -*- coding: utf-8 -*-
"""La auditoría de paridad no debe evaluarnos con pasadas DIURNAS de MIROVA.

POR QUÉ (el fenómeno): de día el Sol reflejado en nubes y nieve entra en la
banda MIR de 3,7-4 µm con intensidad comparable a la de un foco incandescente.
El sensor no distingue "caliente" de "brillante", así que MIROVA publica de vez
en cuando alertas diurnas que son reflexión, no volcán (A76). Nuestro pipeline
descarta el diurno por diseño (`_reject_daytime`, store.py).

El problema: la auditoría semanal cruzaba contra CONS ∪ OCR sin mirar la hora,
así que esas pasadas entraban al DENOMINADOR del recall y nos penalizaban por
no detectar lo que decidimos no mirar. En la ventana S124 eran 82 de 1338
alertas (6,1 %), y en Nevados de Chillán la alerta MÁS GRANDE del período era
diurna.

Estos tests fijan que el filtro de la auditoría sea EXACTAMENTE el del pipeline
(misma función), no un umbral paralelo que pueda divergir.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.store import _reject_daytime, _solar_elevation  # noqa: E402
from scripts.auto_audit_weekly import (bucket_representative_sensor,  # noqa: E402
                                       es_pasada_diurna_descartada)

# Nevados de Chillán y el caso real que motivó el filtro.
NDC = (-36.868, -71.378)
VILLARRICA = (-39.420292, -71.939908)


def _dt(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def test_alerta_diurna_real_de_ndc_queda_descartada():
    """2026-06-12 18:18Z: 0,320 MW, 3,5x mayor que cualquier valor nocturno."""
    assert es_pasada_diurna_descartada("VIIRS375", NDC[0], NDC[1],
                                       _dt("2026-06-12T18:18:00"))


def test_alerta_diurna_real_de_villarrica_queda_descartada():
    """2026-08-17 19:06Z: la que parecía un FN de 1,86 MW y era el sol a +27,8°."""
    assert es_pasada_diurna_descartada("VIIRS375", VILLARRICA[0], VILLARRICA[1],
                                       _dt("2026-08-17T19:06:00"))


def test_la_misma_deteccion_de_noche_SI_cuenta():
    """El mismo 1,86 MW reaparece esa noche: eso sí debe evaluarnos."""
    assert not es_pasada_diurna_descartada("VIIRS375", VILLARRICA[0], VILLARRICA[1],
                                           _dt("2026-08-18T05:48:00"))


def test_el_filtro_es_el_MISMO_del_pipeline_no_uno_paralelo():
    """Si alguien cambia la regla del pipeline, la auditoría debe seguirla sola."""
    from pipeline.profile import ENABLE_DAYTIME_MODIS
    for bucket in ("MODIS", "VIIRS375", "VIIRS750"):
        for ts in ("2026-06-12T18:18:00", "2026-08-18T05:48:00",
                   "2026-01-15T16:00:00", "2026-01-15T08:00:00"):
            dt = _dt(ts)
            elev = _solar_elevation(NDC[0], NDC[1], dt)
            esperado = _reject_daytime(bucket_representative_sensor(bucket),
                                       elev, ENABLE_DAYTIME_MODIS)
            assert es_pasada_diurna_descartada(bucket, NDC[0], NDC[1], dt) == esperado


def test_bucket_a_sensor_respeta_la_convencion_del_proyecto():
    """A48: la convención real es VIIRS_* sin sufijo = I-band 375 m."""
    assert bucket_representative_sensor("MODIS").startswith("MODIS")
    assert not bucket_representative_sensor("VIIRS375").startswith("MODIS")
    assert not bucket_representative_sensor("VIIRS750").startswith("MODIS")


def test_noche_profunda_nunca_se_descarta():
    for bucket in ("MODIS", "VIIRS375", "VIIRS750"):
        assert not es_pasada_diurna_descartada(bucket, NDC[0], NDC[1],
                                               _dt("2026-06-12T05:00:00"))
