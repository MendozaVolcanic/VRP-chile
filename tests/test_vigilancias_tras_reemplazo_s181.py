# -*- coding: utf-8 -*-
"""S181: las vigilancias de las guardias K siguen mirando después de reemplazar la historia con la vía.

POR QUÉ. El reemplazo de la historia (#987) escribe en `data/mirova_equivalent/` records de la vía reprocesados (perfil
`_s172_retro_paquete`, `processed_utc` del reproceso). Simulado sobre main `8250b68f1` el 2026-11-12
(`D:\\vrp-trabajo\\temporales\\s181_sospecha\\`), dejaba las tres vigilancias en VIGILANCIA_CIEGA:
- el encendido de VIIRS 375 y 750 pasaba del 2026-11-11 13:4x al 2026-11-08 18:04 (el `processed_utc` del reproceso), lo
  que metía noches reprocesadas en el plazo de 29 protegidas de la reversión (6 y 4 «vistas» que no eran del NRT);
- el nulo (guardia K contra producción K en los 14 días previos al encendido) pasaba de 167, 274 y 270 pares a 0, porque
  esa ventana queda toda con la vía (punto 4 de docs/AUDIT_S179.md, decisión 6).
Arreglo: el encendido se lee sólo de records escritos por producción, y el nulo medido antes del reemplazo queda sellado
(`experiments/_s181_guardias_reemplazo/nulo_sellado.json`) y se usa cuando la ventana ya no tiene pares K.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import vigilancia_guardia_modis as vg  # noqa: E402

REPROCESO = {"perfil": "_s172_retro_paquete"}
PRODUCCION = {"perfil": "mirova_equivalent"}


# ------------------------------------------------------------------ encendido
@pytest.mark.parametrize("sensor,plat", [("MODIS", "MODIS_AQUA"), ("VIIRS375", "VIIRS_NOAA20"),
                                         ("VIIRS750", "VIIRS_NOAA21_750")])
def test_el_encendido_ignora_los_records_del_reproceso(sensor, plat):
    raw = {"NevadosDeChillan": [
        # historia reemplazada: la vía, pero reprocesada antes del encendido
        {"sensor": plat, "datetime_utc": "2025-03-01 06:30", "via_codigo_mirova": True, "regimen": REPROCESO,
         "processed_utc": "2026-11-08T18:04:23Z"},
        # la primera pasada que escribió el NRT con la vía encendida
        {"sensor": plat, "datetime_utc": "2026-11-11 06:54", "via_codigo_mirova": True, "regimen": PRODUCCION,
         "processed_utc": "2026-11-11T13:45:35Z"}]}
    e = vg.encendido_desde_datos(raw, sensor=sensor)
    assert e["encendido_utc"] == "2026-11-11 13:45:35"
    # el record reprocesado sigue siendo de la vía para el pareo (no es K: no entra al nulo)
    assert ("NevadosDeChillan", plat, "2025-03-01 06:30") in e["via"]


def test_un_record_sin_regimen_sigue_contando_para_el_encendido():
    """Control: los records sin `regimen` (anteriores a la marca de régimen, #785) los escribió producción."""
    raw = {"Lascar": [{"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-03 03:10", "via_codigo_mirova": True,
                       "processed_utc": "2026-11-03T05:00:00Z"}]}
    assert vg.encendido_desde_datos(raw)["encendido_utc"] == "2026-11-03 05:00:00"


# ------------------------------------------------------------------ nulo sellado
SELLO = {"MODIS": {"encendido_utc": "2026-11-02 20:11:43", "pares": 167, "distintas": 0, "detalle": [],
                   "medido_en_commit": "8250b68f1"}}
SIN_MEDIR = {"pares": 0, "distintas": 0, "detalle": [], "sin_medir": True, "nota": "x"}


def test_el_nulo_sellado_reemplaza_al_nulo_sin_pares():
    n = vg.nulo_vigente(SIN_MEDIR, "MODIS", "2026-11-02 20:11:43", sellado=SELLO)
    assert n["pares"] == 167 and n["distintas"] == 0 and n["sin_medir"] is False and n["sellado"] is True
    assert vg.avisos_nulo(n) == []


def test_un_nulo_medido_no_lo_tapa_el_sello():
    vivo = {"pares": 12, "distintas": 1, "detalle": [{"volcano": "Lascar"}], "sin_medir": False, "nota": "x"}
    assert vg.nulo_vigente(vivo, "MODIS", "2026-11-02 20:11:43", sellado=SELLO) is vivo


def test_el_sello_de_otro_encendido_no_vale():
    """Si la vía se apaga y se vuelve a encender, el nulo del encendido viejo no sirve: sigue el aviso."""
    n = vg.nulo_vigente(SIN_MEDIR, "MODIS", "2026-12-01 10:00:00", sellado=SELLO)
    assert n["sin_medir"] is True and vg.avisos_nulo(n)


def test_un_sello_con_pasadas_distintas_no_tapa_el_investigar():
    """Verificador S181 (O4): el sello se aplica después de `disparadores`; uno con distintas no puede dar VERDE."""
    sucio = {"MODIS": dict(SELLO["MODIS"], distintas=2, detalle=[{"volcano": "Lascar"}] * 2)}
    n = vg.nulo_vigente(SIN_MEDIR, "MODIS", "2026-11-02 20:11:43", sellado=sucio)
    assert n["sin_medir"] is True and vg.avisos_nulo(n)


def test_sin_sello_del_sensor_sigue_el_aviso():
    n = vg.nulo_vigente(SIN_MEDIR, "VIIRS375", "2026-11-11 13:45:35", sellado=SELLO)
    assert n["sin_medir"] is True and vg.avisos_nulo(n)


def test_el_sello_commiteado_tiene_los_tres_sensores_con_pares():
    with open(vg.NULO_SELLADO, encoding="utf-8") as f:
        s = json.load(f)
    assert set(s) == {"MODIS", "VIIRS375", "VIIRS750"}
    for sensor, n in s.items():
        assert n["pares"] > 0, sensor          # un sello de 0 pares sería sellar «no medí»
        assert n["distintas"] == 0, sensor      # sólo se sella un nulo limpio
        assert len(n["encendido_utc"]) == 19 and n["medido_en_commit"]
