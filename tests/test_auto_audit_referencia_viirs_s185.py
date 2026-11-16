# -*- coding: utf-8 -*-
"""S185: el guard de «referencia sospechosa» (A119) cubre a cualquier VIIRS, no sólo a Suomi NPP.

POR QUÉ. El defecto de Mirova-v1 que A119 documenta (antes del 2026-10-09 la distancia y la clase de una fila SÓLO OCR
pueden venir de la imagen de otra pasada) es del scraper de OCR, no de una plataforma. El guard de S166 preguntaba si
NUESTRO record de la pasada era de Suomi NPP ("SNPP" en el nombre del sensor), así que una fila con el mismo patrón de
NOAA-20 o NOAA-21 seguía levantando flag. Caso real: Láscar VIIRS 375 2026-10-01 05:18 UTC (NOAA-21, MIROVA 1,2 MW),
el único flag de la auditoría del 2026-11-15, con la fila sólo OCR procesada 8 h 43 min después de la pasada.
La fecha de corte no cambia (la de la pasada, HITO_OCR_SUOMI_NPP), ni las demás condiciones del guard.
Verificación independiente: D:\\vrp-trabajo\\temporales\\s185_aparte_verif\\DETALLE.txt (A3) y s185_audit_verif\\VERIFICACION.md.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.auto_audit_weekly as aa  # noqa: E402

FRONTERA = "2026-09-18"
WIN = ("2026-08-27", "2026-10-26")


def _fila(vol, b, fecha, vrp, source="OCR"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp,
            "tipo": "ALERTA_TERMICA_OCR" if source == "OCR" else "ALERTA_TERMICA", "source": source, "dist_km": None}


def _brec(vol, b, fecha, sensor):
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10], "pub": False, "sha": "abc", "sensor": sensor}


def _lista(filas, recs):
    return aa.alertas_protegidas(filas, recs, WIN, FRONTERA, diurna=lambda *a: False)


@pytest.mark.parametrize("b,sensor", [
    ("VIIRS375", "VIIRS_SNPP"),            # lo de S166
    ("VIIRS375", "VIIRS_NOAA20"),
    ("VIIRS375", "VIIRS_NOAA21"),          # Láscar 2026-10-01 05:18
    ("VIIRS750", "VIIRS_SNPP_750"),
    ("VIIRS750", "VIIRS_NOAA20_750"),
    ("VIIRS750", "VIIRS_NOAA21_750"),
])
def test_solo_ocr_antes_del_hito_es_sospechosa_en_cualquier_viirs(b, sensor):
    filas = [_fila("Lascar", b, "2026-10-01 05:18:00", 1.2)]
    lista = _lista(filas, [_brec("Lascar", b, "2026-10-01 05:18", sensor)])
    assert [(p["estado"], p["referencia_sospechosa"]) for p in lista] == [("sin_publicar", True)]
    assert aa.flags_protegidas(lista, "K") == [], "una sospechosa no levanta flag"
    aparte = aa.protegidas_aparte(lista, "K")
    assert len(aparte) == 1 and "Lascar" in aparte[0] and "referencia sospechosa" in aparte[0]
    assert "sólo OCR de VIIRS" in aparte[0]


@pytest.mark.parametrize("fila,sensor", [
    # controles: cada condición del guard sigue siendo necesaria, el cambio no apaga el flag en general
    (_fila("Lascar", "VIIRS375", "2026-10-01 05:18:00", 1.2, source="CONS"), "VIIRS_NOAA21"),   # de la tabla
    (_fila("Lascar", "VIIRS375", "2026-10-09 05:18:00", 1.2, source="OCR"), "VIIRS_NOAA21"),    # en el hito (no antes)
    (_fila("Lascar", "VIIRS375", "2026-10-12 05:18:00", 1.2, source="OCR"), "VIIRS_NOAA21"),    # después del hito
    (_fila("Lascar", "MODIS", "2026-10-01 05:18:00", 1.2, source="OCR"), "MODIS_AQUA"),         # no es VIIRS
    (_fila("Lascar", "MODIS", "2026-10-01 05:18:00", 1.2, source="OCR"), "MODIS_TERRA"),
])
def test_control_la_protegida_normal_sigue_siendo_flag(fila, sensor):
    b = fila["sensor_bucket"]
    lista = _lista([fila], [_brec("Lascar", b, fila["fecha_utc"][:16], sensor)])
    assert lista[0]["referencia_sospechosa"] is False
    flags = aa.flags_protegidas(lista, "K")
    assert len(flags) == 1 and f"Lascar {b}" in flags[0]
    assert aa.protegidas_aparte(lista, "K") == []


def test_control_mezcla_de_tabla_y_ocr_en_la_misma_pasada_no_es_sospechosa():
    """Si la tabla (CONS) también la tiene, la fila no es sólo OCR: el guard no aplica."""
    filas = [_fila("Lascar", "VIIRS375", "2026-10-01 05:18:00", 1.2, source="OCR"),
             _fila("Lascar", "VIIRS375", "2026-10-01 05:18:00", 1.2, source="CONS")]
    lista = _lista(filas, [_brec("Lascar", "VIIRS375", "2026-10-01 05:18", "VIIRS_NOAA21")])
    assert lista[0]["referencia_sospechosa"] is False
    assert len(aa.flags_protegidas(lista, "K")) == 1
