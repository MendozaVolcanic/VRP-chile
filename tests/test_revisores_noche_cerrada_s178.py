# -*- coding: utf-8 -*-
"""S178: los revisores de la guardia K (VIIRS y MODIS) y de la sombra no juzgan un día UTC sin su noche cerrada, y una
corrida que escribe 0 porque la noche ya estaba escrita no cuenta como corrida muerta.

POR QUÉ (bitácora tasks/LOOP_OBJETIVOS.md de loop/activo, entrada «2026-11-10 03:28 UTC (S178)»). La guardia K de VIIRS
corrió dos veces el 2026-11-10 (runs 42734558894 a las 01:16 UTC y 42742205624 a las 02:21 UTC) y quedó 11 de 11 en
rojo con los datos escritos en main. Dos causas: (1) la ventana termina en el día UTC en curso, cuya noche chilena aún
no había pasado («2026-11-10: sin pasada a la vez ... catálogo de CMR vacío»); (2) la segunda corrida no tenía nada
nuevo que escribir y el revisor exigía algún record. La sombra del 2026-11-09 23:42 UTC cayó por (1) en Chillán,
Copahue y Llaima. La guardia necesita 3 noches verdes seguidas para que Nicolás pueda encender la vía de VIIRS.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Los casos de falso rojo dan rojo contra el código de origin/main e7cfbaf54
(salida anotada en el PR). (2) Los controles (día cerrado sin datos, corrida que no escribe una noche que nadie
escribió, record con otro sha, ventana sin ninguna noche cerrada) dan rojo antes y después: el arreglo no deja ciego
al revisor.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import revisar_guardia_modis as RGM  # noqa: E402
import revisar_guardia_viirs as RGV  # noqa: E402
import revisar_sombra as RS  # noqa: E402

# --------------------------------------------------------------------------------------------- guardia K de VIIRS
PLAT_V = ("VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750")
COB_V = {"fallas": [], "plataformas": {p: {} for p in PLAT_V}, "incidencias": []}


def _kv(dia, sensor, proc, sha="abc", perfil="guardia_k_viirs"):
    return {"datetime_utc": "2026-11-%02d 06:10" % dia, "sensor": sensor, "processed_utc": proc,
            "regimen": {"perfil": perfil, "codigo_sha": sha}}


def _noches_v(desde_dia, hasta_dia, proc, sha="abc"):
    out = []
    for d in range(desde_dia, hasta_dia + 1):
        out += [_kv(d, "VIIRS_NOAA20", proc, sha), _kv(d, "VIIRS_NOAA20_750", proc, sha)]
    return out


def _sin_granulos(cob, fecha, plataformas):
    return dict(cob, incidencias=[{"tipo": "sin_granulos", "fecha": fecha, "plataforma": p} for p in plataformas])


def _rev_v(recs, desde, ini="2026-11-03", fin="2026-11-10", cob=COB_V, sha="abc"):
    return RGV.revisar(recs, "", ini, fin, desde, cob, sha=sha)


# ---- falso rojo (1): el día UTC en curso, sin su noche todavía
def test_v_dia_en_curso_sin_noche_no_se_juzga_aunque_la_busqueda_responda_vacia():
    """Run 42734558894 (01:16 UTC del 11-10): escribió del 11-03 al 11-09; el 11-10 buscó y CMR no tenía nada."""
    desde = "2026-11-10T01:16:00Z"
    recs = _noches_v(3, 9, "2026-11-10T01:40:00Z")
    cob = _sin_granulos(COB_V, "2026-11-10", PLAT_V)
    ok, resumen = _rev_v(recs, desde, cob=cob)
    assert ok is True, resumen
    assert "2026-11-10" in resumen and "noche" in resumen, resumen   # se dice que no se juzgó, no se calla


def test_v_dia_en_curso_sin_noche_no_se_juzga_aunque_no_haya_prueba():
    ok, resumen = _rev_v(_noches_v(3, 9, "2026-11-10T01:40:00Z"), "2026-11-10T01:16:00Z")
    assert ok is True, resumen


# ---- falso rojo (2): segunda corrida del mismo día, la noche ya estaba escrita
def test_v_segunda_corrida_que_no_escribe_porque_la_noche_ya_estaba_escrita_es_verde():
    """Run 42742205624 (02:21 UTC del 11-10): la de las 01:16 ya había escrito todas las noches cerradas."""
    ok, resumen = _rev_v(_noches_v(3, 9, "2026-11-10T01:40:00Z"), "2026-11-10T02:21:00Z")
    assert ok is True, resumen


def test_v_segunda_corrida_de_la_tarde_con_la_noche_de_hoy_ya_escrita_es_verde():
    """Un despacho a mano a las 15:00 escribió la noche del 11-10; el cron de las 19:35 no tiene nada nuevo."""
    recs = _noches_v(3, 10, "2026-11-10T15:20:00Z")
    ok, resumen = _rev_v(recs, "2026-11-10T19:35:00Z")
    assert ok is True, resumen


# ---- controles: el revisor sigue pudiendo dar rojo
def test_v_control_dia_cerrado_sin_datos_sigue_rojo():
    """19:35 UTC del 11-10: la noche del 11-10 ya cerró y nadie la escribió ni probó que no hubo pasada."""
    ok, resumen = _rev_v(_noches_v(3, 9, "2026-11-10T01:40:00Z"), "2026-11-10T19:35:00Z")
    assert ok is False and "2026-11-10" in resumen, resumen


def test_v_control_dia_cerrado_con_catalogo_vacio_sigue_rojo():
    cob = _sin_granulos(COB_V, "2026-11-10", PLAT_V)
    ok, resumen = _rev_v(_noches_v(3, 9, "2026-11-10T01:40:00Z"), "2026-11-10T19:35:00Z", cob=cob)
    assert ok is False and "catálogo" in resumen, resumen
    # un catálogo vacío tampoco excusa haber escrito 0: la noche del 11-10 queda pendiente
    assert "no escribió" in resumen and "noches cerradas de la ventana ya estaban escritas" not in resumen, resumen


def test_v_control_corrida_que_no_escribe_una_noche_que_nadie_escribio_sigue_roja():
    """El 11-08 no lo escribió nadie y esta corrida tampoco: es corrida muerta, no «ya estaba escrita»."""
    recs = [r for r in _noches_v(3, 9, "2026-11-10T01:40:00Z") if not r["datetime_utc"].startswith("2026-11-08")]
    ok, resumen = _rev_v(recs, "2026-11-10T02:21:00Z")
    assert ok is False and "no escribió" in resumen and "2026-11-08" in resumen, resumen


def test_v_control_un_solo_sensor_pendiente_sigue_rojo():
    """VIIRS 750 del 11-09 no lo escribió nadie: VIIRS 375 al día no tapa al otro sensor."""
    recs = [r for r in _noches_v(3, 9, "2026-11-10T01:40:00Z")
            if not (r["datetime_utc"].startswith("2026-11-09") and r["sensor"].endswith("_750"))]
    ok, resumen = _rev_v(recs, "2026-11-10T02:21:00Z")
    assert ok is False and "ningún record de VIIRS750 escrito" in resumen, resumen


def test_v_control_record_de_esta_hora_con_otro_sha_no_cuenta_como_ya_escrito():
    """Escrito después del inicio de la corrida pero con otro sha: ni de esta corrida ni de una anterior."""
    recs = _noches_v(3, 9, "2026-11-10T01:40:00Z") + _noches_v(10, 10, "2026-11-10T19:50:00Z", sha="otro")
    ok, resumen = _rev_v(recs, "2026-11-10T19:35:00Z")
    assert ok is False and "no escribió" in resumen, resumen


def test_v_control_ventana_sin_ninguna_noche_cerrada_es_roja():
    """Un despacho con sólo el día en curso antes de las 12 UTC no juzga nada: no puede salir verde."""
    ok, resumen = _rev_v([], "2026-11-10T01:16:00Z", ini="2026-11-10", fin="2026-11-10")
    assert ok is False and "nada que juzgar" in resumen, resumen


def test_v_frontera_de_la_noche_cerrada():
    recs = _noches_v(3, 9, "2026-11-10T01:40:00Z")
    antes = _rev_v(recs, "2026-11-10T%02d:59:59Z" % (RS.HORA_NOCHE_CERRADA_UTC - 1))
    justo = _rev_v(recs, "2026-11-10T%02d:00:00Z" % RS.HORA_NOCHE_CERRADA_UTC)
    assert antes[0] is True, antes[1]
    assert justo[0] is False and "2026-11-10" in justo[1], justo[1]


# --------------------------------------------------------------------------------------------- guardia K de MODIS
COB_M = {"fallas": [], "plataformas": {"MODIS_TERRA": {}, "MODIS_AQUA": {}}, "incidencias": []}


def _km(dia, proc, sha="abc"):
    return {"datetime_utc": "2026-11-%02d 02:40" % dia, "sensor": "MODIS_TERRA", "processed_utc": proc,
            "regimen": {"perfil": "guardia_k_modis", "codigo_sha": sha}}


def test_m_dia_en_curso_y_segunda_corrida_son_verdes():
    recs = [_km(d, "2026-11-10T01:40:00Z") for d in range(3, 10)]
    ok, resumen = RGM.revisar(recs, "", "2026-11-03", "2026-11-10", "2026-11-10T02:21:00Z", COB_M, sha="abc")
    assert ok is True, resumen


def test_m_control_dia_cerrado_sin_datos_sigue_rojo():
    recs = [_km(d, "2026-11-10T01:40:00Z") for d in range(3, 10)]
    ok, resumen = RGM.revisar(recs, "", "2026-11-03", "2026-11-10", "2026-11-10T17:40:00Z", COB_M, sha="abc")
    assert ok is False and "2026-11-10" in resumen and "no escribió" in resumen, resumen


# ----------------------------------------------------------------------------------------------------- la sombra
PLAT_S = ("MODIS_TERRA", "MODIS_AQUA", "VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750")
COB_S = {"fallas": [], "plataformas": {p: {} for p in PLAT_S}, "incidencias": []}
FAM_S = {"MODIS": "MODIS_AQUA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}


def _vs(dia, sensor, proc, sha="abc"):
    return {"datetime_utc": "2026-11-%02d 06:12" % dia, "sensor": sensor, "via_codigo_mirova": True,
            "processed_utc": proc, "regimen": {"perfil": "sombra_codigo_mirova", "codigo_sha": sha}}


def _noches_s(desde_dia, hasta_dia, proc, sha="abc"):
    return [_vs(d, s, proc, sha) for d in range(desde_dia, hasta_dia + 1) for s in FAM_S.values()]


def test_s_corrida_que_cruza_la_medianoche_no_juzga_el_dia_nuevo():
    """La sombra del 11-09 23:42 UTC: el job de Chillán arrancó pasada la medianoche y juzgó el 11-10 sin noche."""
    recs = _noches_s(3, 8, "2026-11-09T15:20:00Z") + _noches_s(9, 9, "2026-11-10T00:20:00Z")
    cob = _sin_granulos(COB_S, "2026-11-10", PLAT_S[2:])
    ok, resumen = RS.revisar(recs, "", "2026-11-03", "2026-11-10", "2026-11-10T00:05:00Z", cob, sha="abc")
    assert ok is True, resumen


def test_s_segunda_corrida_sin_nada_nuevo_es_verde():
    recs = _noches_s(3, 10, "2026-11-10T15:20:00Z")
    ok, resumen = RS.revisar(recs, "", "2026-11-03", "2026-11-10", "2026-11-10T20:00:00Z", COB_S, sha="abc")
    assert ok is True, resumen


def test_s_control_dia_cerrado_sin_datos_sigue_rojo():
    recs = _noches_s(3, 9, "2026-11-09T15:20:00Z")
    ok, resumen = RS.revisar(recs, "", "2026-11-03", "2026-11-10", "2026-11-10T15:01:00Z", COB_S, sha="abc")
    assert ok is False and "2026-11-10" in resumen and "no produjo nada" in resumen, resumen


def test_s_control_catalogo_vacio_de_viirs_no_excusa_haber_escrito_cero():
    recs = _noches_s(3, 9, "2026-11-09T15:20:00Z") + [_vs(10, FAM_S["MODIS"], "2026-11-09T15:20:00Z")]
    cob = _sin_granulos(COB_S, "2026-11-10", PLAT_S[2:])
    ok, resumen = RS.revisar(recs, "", "2026-11-03", "2026-11-10", "2026-11-10T15:01:00Z", cob, sha="abc")
    assert ok is False and "catálogo" in resumen and "no produjo nada" in resumen, resumen


def test_s_control_ventana_sin_ninguna_noche_cerrada_es_roja():
    ok, resumen = RS.revisar([], "", "2026-11-10", "2026-11-10", "2026-11-10T03:00:00Z", COB_S, sha="abc")
    assert ok is False and "nada que juzgar" in resumen, resumen


# ------------------------------------------------------------------------------------- la hora, anclada al código
def test_la_latencia_es_la_de_fetch():
    """La hora de cierre suma la latencia mínima de LANCE que usa pipeline/fetch.py::dia_incompleto."""
    from pipeline.fetch import LATENCIA_MINIMA_NRT_H
    assert RS.LATENCIA_NRT_H == LATENCIA_MINIMA_NRT_H
    assert RS.HORA_NOCHE_CERRADA_UTC == RS.ULTIMA_PASADA_NOCTURNA_UTC_H + RS.LATENCIA_NRT_H


def test_las_dos_guardias_usan_la_misma_regla_que_la_sombra():
    assert RGM.noche_cerrada is RS.noche_cerrada
