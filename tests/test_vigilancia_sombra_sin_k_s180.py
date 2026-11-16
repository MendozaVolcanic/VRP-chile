"""S180 (issue #989): la vigilancia de la sombra no exige frescura de K cuando ningún sensor de producción sigue en K.

POR QUÉ. Desde S176 la vigilancia sólo exige que produzca K en los sensores que siguen con K (`sensores_de_k`): los que ya
tienen records de la vía no se miran, porque su K se apagó a propósito. Con el encendido de la vía en VIIRS 375 y 750
(#974 y #983, 2026-11-11) los tres sensores quedaron con la vía y `sensores_de_k` devolvió una lista vacía. La frescura
leía `sensores = sensores or aa.SENSORS`: una lista vacía es falsa en Python y volvía al valor por defecto, los tres
sensores. Resultado: el issue #989 («vigilancia ciega», MODIS sin K desde el 2026-11-01 en los 11 Tier A) y, tres días
después, lo mismo en VIIRS. Una lista vacía quiere decir «ningún sensor que vigilar», no «no me dijeron cuáles».

QUÉ VIGILA.
1. Con `sensores=[]` la frescura de producción no da avisos, aunque los records de K tengan semanas.
2. Control: con `sensores=None` (sin vía en ningún sensor, lo de antes) sigue exigiendo los tres sensores; con un sensor
   en K sigue avisando por ese sensor. Así la prueba no pasa por haber apagado el aviso entero.
3. Cuando los tres sensores tienen records de la vía, `sensores_de_k` da la lista vacía (la entrada real del caso).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Sin el arreglo, el caso 1 da dos avisos (MODIS viejo y VIIRS750 sin records),
reproducido sobre main `fa90366e8`. (2) Los controles del punto 2 tienen que dar avisos: si dan cero, la prueba cae.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import vigilancia_sombra as vs  # noqa: E402

HOY = "2026-11-12"
# K de producción de Láscar: MODIS terminó el 2026-11-01 (vía desde S172), VIIRS 375 el 2026-11-11 (vía desde #974);
# VIIRS 750 sin records de K en la ventana.
RECS = [{"vol": "Lascar", "b": "MODIS", "noche": "2026-11-01"},
        {"vol": "Lascar", "b": "VIIRS375", "noche": "2026-11-11"}]


def test_sin_sensores_en_k_no_hay_avisos_de_produccion():
    assert vs.avisos_produccion(RECS, HOY, vols=["Lascar"], sensores=[]) == []


def test_control_sin_via_sigue_exigiendo_los_tres_sensores():
    av = vs.avisos_produccion(RECS, HOY, vols=["Lascar"], sensores=None)
    assert any("en MODIS no produce hace 11 días" in a for a in av), av
    assert any("de Lascar en VIIRS750 en la ventana" in a for a in av), av
    assert not any("VIIRS375" in a for a in av), av


def test_control_un_sensor_en_k_sigue_avisando_por_ese_sensor():
    av = vs.avisos_produccion(RECS, HOY, vols=["Lascar"], sensores=["MODIS"])
    assert len(av) == 1 and "en MODIS no produce" in av[0], av


def test_tres_sensores_con_via_dejan_la_lista_de_k_vacia():
    via = {("Lascar", "MODIS_AQUA", "2026-11-02 18:10"), ("Lascar", "VIIRS_NOAA20", "2026-11-11 06:54"),
           ("Lascar", "VIIRS_NOAA20_750", "2026-11-11 06:54")}
    assert vs.sensores_de_k(via) == []
