# -*- coding: utf-8 -*-
"""S194 (auditoría externa Codex, Cierre I, hallazgo C1-101): la protegida de la que producción no tiene record y que la
guardia K tampoco publica avisa el mismo día.

POR QUÉ, COMO GEÓLOGO. Una alerta protegida de MIROVA (1 MW o más, lectura A) que no aparece en el tablero es lo más
grave para el operador, y da lo mismo si la vía «código MIROVA» miró la pasada y calló o si ni siquiera la tiene (el
gránulo de borde que la vía descarta, 171-01, o un gránulo perdido): en los dos casos MIROVA ve un cráter y nosotros no.
La vigilancia diaria de la guardia avisaba la primera (S193, `protegidas_sin_publicar_sin_aviso`) y, de la segunda, sólo
la que la guardia K publicaba después del encendido (`protegidas_sin_record_produccion`, MA172-202). Si la guardia
tampoco tenía la pasada, o K también callaba, el JSON salía VERDE sin lista y el único aviso era el del auto-audit del
lunes (`auto_audit_weekly.avisos_protegidas_sin_record`), hasta 7 días después. El caso real es Chaitén MODIS
2026-11-19 02:30 UTC, MIROVA 1,07 MW (verificación de Cierre I, instrumento A).

QUÉ NO DEBE AVISAR. Una pasada que producción no procesa a propósito no es silencio: la de día de VIIRS (flag apagado) y
la de día de MODIS anterior a la frontera de los datos (#1090) las quita `pasadas_de_alerta` con
`auto_audit_weekly.es_pasada_diurna_descartada`, la misma regla del auto-audit (A102, no se copia). Y una pasada sin
record no se lee antes de ESPERA_SIN_RECORD_H horas, porque el NRT procesa con atraso.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Cada caso tiene su control con la misma escena y el resultado contrario (la
pasada publicada, de día, dentro de la espera, ya juzgada). (2) Antes del arreglo las pruebas de aviso caen por
aserción (la lista sale vacía), comprobado sobre main `852279400`.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import pipeline.profile as prof  # noqa: E402
import scripts.vigilancia_guardia_modis as vg  # noqa: E402  (el mismo módulo que parchea el fixture `disco`)
from test_vigilancia_guardia_por_volcan_s175 import (  # noqa: E402,F401  (fixture `disco` y la escena de S175)
    ALERTA, REF_FRESCA, _disco_base, _fila, disco)

vs = vg.vs          # la instancia de vigilancia_sombra que usa vg (C1-106: una sola instancia por prueba)
aa = vg.aa
ENC = "2026-11-05 22:10:00"
AHORA = "2026-11-21 23:00:00"


def _pasada(vol, fecha, protegida, prod, guardia, sensor="MODIS", vrp=None):
    return {"volcano": vol, "sensor": sensor, "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": vrp if vrp is not None else (1.07 if protegida else 0.3), "protegida": protegida,
            "minima": False, "referencia_sospechosa": False, "prod_pub": prod, "guardia_pub": guardia,
            "prod_via": None if prod is None else True, "prod_caida_k": None}


def _disp(pas, juzgadas=None, sensor="MODIS", ahora=AHORA):
    return vg.disparadores(list(pas), [], [], hoy=ahora[:10], encendido=ENC, juzgadas=juzgadas, ahora=ahora,
                           sensor=sensor)


def _sin_aviso(d):
    return [(p["volcano"], p["fecha_utc"], p["prod_pub"]) for p in d["protegidas_sin_publicar_sin_aviso"]]


# ------------------------------------------------------------------ el hueco de C1-101
@pytest.mark.parametrize("guardia", [None, False])
def test_c1_101_sin_record_y_la_guardia_no_la_publica_avisa(guardia):
    """Chaitén 2026-11-19 02:30: producción no tiene record y la guardia no tiene la pasada o tampoco la publica."""
    d = _disp([_pasada("Chaiten", "2026-11-19 02:30", True, None, guardia)])
    assert _sin_aviso(d) == [("Chaiten", "2026-11-19 02:30", None)]
    assert d["veredicto"] == "VERDE", "es un aviso aparte: el veredicto de la regla no cambia"
    assert d["reversion"] == [] and d["protegidas_sin_record_produccion"] == []
    # control: la misma pasada con record publicado no avisa
    assert _sin_aviso(_disp([_pasada("Chaiten", "2026-11-19 02:30", True, True, guardia)])) == []


def test_c1_101_una_muy_bajo_sin_record_no_es_este_aviso():
    assert _sin_aviso(_disp([_pasada("Chaiten", "2026-11-19 02:30", False, None, None)])) == []


def test_c1_101_dentro_de_la_espera_del_nrt_no_avisa():
    """El NRT procesa con atraso: una pasada sin record de hace menos de ESPERA_SIN_RECORD_H horas todavía no es silencio."""
    p = _pasada("Chaiten", "2026-11-21 02:30", True, None, None)
    assert _sin_aviso(_disp([p], ahora="2026-11-21 23:00:00")) == []
    # control: pasada la espera, avisa
    assert _sin_aviso(_disp([p], ahora="2026-11-22 03:00:00")) == [("Chaiten", "2026-11-21 02:30", None)]


def test_c1_101_lo_que_ya_pide_investigar_no_se_repite():
    """Sin record y la guardia la publica después del encendido: ya es `protegidas_sin_record_produccion` (INVESTIGAR)."""
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, None, True)])
    assert d["veredicto"] == "INVESTIGAR" and [p["fecha_utc"] for p in d["protegidas_sin_record_produccion"]] == [
        "2026-11-19 06:00"]
    assert _sin_aviso(d) == []
    # control: la misma escena antes del encendido no la cubre ningún nivel y va al aviso
    d = _disp([_pasada("Lascar", "2026-11-04 06:00", True, None, True)])
    assert d["protegidas_sin_record_produccion"] == [] and _sin_aviso(d) == [("Lascar", "2026-11-04 06:00", None)]


def test_c1_101_una_pasada_juzgada_deja_de_avisar():
    p = _pasada("Chaiten", "2026-11-19 02:30", True, None, None)
    assert _sin_aviso(_disp([p], juzgadas={vs._clave(p): {"decision": "granulo perdido"}})) == []


def test_c1_101_el_aviso_es_por_sensor_en_viirs():
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, None, None, sensor="VIIRS750")], sensor="VIIRS750")
    assert _sin_aviso(d) == [("Lascar", "2026-11-19 06:00", None)] and d["veredicto"] == "VERDE"


def test_c1_101_sin_publicar_sigue_avisando_igual():
    """Lo de S193 no cambia: con record que calla y K que también calla, el aviso sale con `prod_pub` False."""
    d = _disp([_pasada("Chaiten", "2026-11-19 02:30", True, False, False)])
    assert _sin_aviso(d) == [("Chaiten", "2026-11-19 02:30", False)]


# ------------------------------------------------------------------ lo que no procesamos a propósito
def _fila_b(vol, fecha, vrp, b):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": "ALERTA_TERMICA",
            "source": "CONS"}


def _avisos_desde_filas(filas, sensor, inicio_dia_modis=None):
    """Recorre pasadas_modis con la regla de día REAL del auto-audit (vs._diurna_por_defecto) y luego disparadores."""
    win = ("2026-11-01", "2026-11-22")
    with patch.object(prof, "ENABLE_DAYTIME_MODIS", True), patch.object(prof, "ENABLE_DAYTIME_VIIRS", False), \
            patch.dict(aa._INICIO_DIA_MODIS, clear=True):
        aa.fijar_inicio_dia_modis(inicio_dia_modis)
        pas = vg.pasadas_modis(filas, [], [], win, diurna=vs._diurna_por_defecto(), sensor=sensor)
    return [(p[0], p[1]) for p in _sin_aviso(_disp(pas, sensor=sensor))]


def test_c1_101_viirs_de_dia_no_avisa():
    """Láscar 2026-11-19 16:00 UTC es mediodía: producción no procesa VIIRS de día (flag apagado). No es silencio."""
    assert _avisos_desde_filas([_fila_b("Lascar", "2026-11-19 16:00:00", 2.0, "VIIRS375")], "VIIRS375") == []
    # control: la misma alerta de noche (06:00 UTC) sí avisa
    assert _avisos_desde_filas([_fila_b("Lascar", "2026-11-19 06:00:00", 2.0, "VIIRS375")], "VIIRS375") == [
        ("Lascar", "2026-11-19 06:00")]


def test_c1_101_modis_de_dia_cuenta_solo_desde_la_frontera_de_los_datos():
    """#1090: producción procesa MODIS de día desde su primer record diurno. Antes, la pasada diurna no es silencio."""
    fila = [_fila_b("NevadosDeChillan", "2026-11-16 15:05:00", 6.98, "MODIS")]
    frontera = datetime(2026, 11, 18, tzinfo=timezone.utc)
    assert _avisos_desde_filas(fila, "MODIS", inicio_dia_modis=frontera) == []
    # control: con la frontera antes de la pasada, la diurna sí nos evalúa y avisa
    frontera = datetime(2026, 11, 15, tzinfo=timezone.utc)
    assert _avisos_desde_filas(fila, "MODIS", inicio_dia_modis=frontera) == [("NevadosDeChillan", "2026-11-16 15:05")]


# ------------------------------------------------------------------ la cadena real desde el disco
def test_c1_101_cadena_real_sin_record_ni_guardia_avisa(disco):
    """Desde los JSON: MIROVA da 25 MW en Chillán y ni producción ni la guardia tienen la pasada."""
    prod, guardia = _disco_base()
    disco(prod, guardia, REF_FRESCA + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0)])
    out = vg.evaluar("2026-11-20")
    assert [(p["volcano"], p["fecha_utc"], p["prod_pub"], p["guardia_pub"])
            for p in out["protegidas_sin_publicar_sin_aviso"]] == [("NevadosDeChillan", ALERTA, None, None)]
    assert out["veredicto"] == "VERDE" and out["protegidas_sin_record_produccion"] == []
    # control: sin la alerta de MIROVA no hay aviso
    disco(*_disco_base(), REF_FRESCA)
    assert vg.evaluar("2026-11-20")["protegidas_sin_publicar_sin_aviso"] == []


def test_c1_101_el_texto_dice_si_produccion_no_tiene_record():
    assert vg.estado_produccion({"prod_pub": None}) == "no tiene record de la pasada"
    assert vg.estado_produccion({"prod_pub": False}) == "no la publica"


def test_c1_101_los_workflows_distinguen_sin_record_de_sin_publicar():
    for wf in ("vigilancia-guardia-modis.yml", "vigilancia-guardia-viirs.yml"):
        texto = (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8")
        bloque = texto[texto.index("> /tmp/sin_aviso.txt"):]
        bloque = bloque[:bloque.index("PY\n")]
        assert "no tiene record de la pasada" in bloque and "no la publica" in bloque, wf
