# -*- coding: utf-8 -*-
"""Decision D-9 (issue #811, Nicolas, 2026-10-15): como se cuentan las alertas de 0,05 MW o menos.

POR QUE. En VIIRS 375 el banner que MIROVA pinta en su imagen dice NONE (sin anomalia) en las 14 pasadas
observadas de 0,04 MW o menos y VERY LOW en las 283 de 0,06 MW o mas; en 0,05 exacto sale de los dos lados
(5 y 5), por el paso de dos decimales del valor publicado (experiments/_s151_alertas_minimas/README.md §2).
El scraper de Mirova-v1 llama ALERTA a todo VRP mayor que cero, asi que 155 pasadas que MIROVA dice no ver
entraban como alertas. Regla decidida: SN ("MIROVA no vio nada": la pasada minima cuenta como lo que dice
el banner), con SE (estrato aparte) y la original informadas al lado en cada evaluacion.

Los tests fijan: la frontera (0,04 y 0,05 minimas, 0,06 y 1,0 no), que 0,05 exacto entra en SN por
defecto pero el umbral 0,04 la deja como alerta (la variante que se informa), que la regla solo toca VIIRS
375, que el VRP de la pasada es el del consolidado antes que el del OCR (el mismo orden del evaluador), que
las alertas protegidas (1 MW o mas, lectura A) no cambian en ningun modo, y el efecto en el etiquetador
(scripts/banco_paridad.py): en SN la noche puede volverse negativo limpio, en SE la pasada sale aparte y la
noche no cambia, y en el modo original nada cambia.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.clase_mirova import (MODO_MINIMAS, MODOS_MINIMAS,  # noqa: E402
                                  TIPO_MINIMA_SE, UMBRAL_MINIMA_MW,
                                  alerta_protegida, aplicar_regla_minimas,
                                  es_alerta_minima, pasadas_protegidas)


def _f(vrp, tipo="ALERTA_TERMICA", sensor="VIIRS375", hora="2026-09-10 05:30:00", source="CONS",
       vol="Lastarria"):
    return {"volcano": vol, "sensor_bucket": sensor, "fecha_utc": hora, "source": source, "tipo": tipo,
            "vrp_mw": vrp, "dist_km": 1.0}


def test_constantes_de_la_decision():
    assert UMBRAL_MINIMA_MW == 0.05
    assert set(MODOS_MINIMAS) == {"SN", "SE", "original"}
    assert MODO_MINIMAS == "SN"


@pytest.mark.parametrize("vrp,esperado", [(0.04, True), (0.05, True), (0.06, False), (1.0, False)])
def test_frontera_viirs375(vrp, esperado):
    assert es_alerta_minima(vrp, "VIIRS375") is esperado


def test_variante_umbral_004_deja_005_como_alerta():
    assert es_alerta_minima(0.04, "VIIRS375", umbral_mw=0.04)
    assert not es_alerta_minima(0.05, "VIIRS375", umbral_mw=0.04)


def test_solo_viirs375():
    # VIIRS 750 tiene su frontera sin resolver (una imagen por lado) y MODIS no tiene alertas en ese rango.
    assert not es_alerta_minima(0.04, "VIIRS750")
    assert not es_alerta_minima(0.04, "MODIS")
    assert not es_alerta_minima(None, "VIIRS375")


def _filas():
    return [_f(0.04, hora="2026-09-10 05:30:00"),
            _f(0.05, hora="2026-09-10 06:10:00"),
            _f(0.06, hora="2026-09-10 07:00:00"),
            _f(1.0, hora="2026-09-10 08:00:00"),
            _f(0.0, tipo="RUTINA", hora="2026-09-10 09:00:00"),
            _f(30.0, tipo="FALSO_POSITIVO", hora="2026-09-10 09:30:00"),
            _f(0.04, sensor="VIIRS750", hora="2026-09-10 05:31:00")]


def test_sn_por_defecto_reescribe_las_minimas_como_rutina():
    filas = _filas()
    out = aplicar_regla_minimas(filas)
    assert [(f["tipo"], f["vrp_mw"]) for f in out.filas] == [
        ("RUTINA", 0.0), ("RUTINA", 0.0), ("ALERTA_TERMICA", 0.06), ("ALERTA_TERMICA", 1.0),
        ("RUTINA", 0.0), ("FALSO_POSITIVO", 30.0), ("ALERTA_TERMICA", 0.04)]
    assert out.minimas == {("Lastarria", "VIIRS375", "2026-09-10 05:30"), ("Lastarria", "VIIRS375", "2026-09-10 06:10")}
    # no muta la entrada
    assert filas[0]["tipo"] == "ALERTA_TERMICA" and filas[0]["vrp_mw"] == 0.04


def test_sn_con_umbral_004_deja_005_como_alerta():
    out = aplicar_regla_minimas(_filas(), "SN", umbral_mw=0.04)
    assert out.filas[1]["tipo"] == "ALERTA_TERMICA" and out.filas[1]["vrp_mw"] == 0.05
    assert out.minimas == {("Lastarria", "VIIRS375", "2026-09-10 05:30")}


def test_se_marca_la_pasada_y_conserva_el_vrp():
    out = aplicar_regla_minimas(_filas(), "SE")
    assert [(f["tipo"], f["vrp_mw"]) for f in out.filas[:3]] == [
        (TIPO_MINIMA_SE, 0.04), (TIPO_MINIMA_SE, 0.05), ("ALERTA_TERMICA", 0.06)]
    assert TIPO_MINIMA_SE.startswith("ALERTA")   # la noche sigue con alerta en SE


def test_original_no_cambia_nada():
    filas = _filas()
    out = aplicar_regla_minimas(filas, "original")
    assert out.filas == filas
    assert len(out.minimas) == 2   # igual informa cuales serian


def test_modo_invalido():
    with pytest.raises(ValueError):
        aplicar_regla_minimas(_filas(), "sn")


def test_una_pasada_es_minima_solo_si_todas_sus_alertas_lo_son():
    # Verificador de #820: la version anterior tomaba el VRP del consolidado y reescribia TODAS las filas de la
    # pasada, asi que una fila del OCR por encima del umbral desaparecia con ella.
    # consolidado 0,06 y OCR 0,04 en la misma pasada: no es minima; nada cambia
    a = [_f(0.06, source="CONS"), _f(0.04, tipo="ALERTA_TERMICA_OCR", source="OCR", hora="2026-09-10 05:30:40")]
    assert [f["tipo"] for f in aplicar_regla_minimas(a).filas] == ["ALERTA_TERMICA", "ALERTA_TERMICA_OCR"]
    # consolidado 0,04 y OCR 0,08: el OCR supera el umbral, no es minima; nada cambia
    b = [_f(0.04, source="CONS"), _f(0.08, tipo="ALERTA_TERMICA_OCR", source="OCR", hora="2026-09-10 05:30:40")]
    out = aplicar_regla_minimas(b)
    assert [f["tipo"] for f in out.filas] == ["ALERTA_TERMICA", "ALERTA_TERMICA_OCR"] and not out.minimas
    # consolidado 0,04 y OCR 0,03: las dos son minimas; las dos filas cambian
    d = [_f(0.04, source="CONS"), _f(0.03, tipo="ALERTA_TERMICA_OCR", source="OCR", hora="2026-09-10 05:30:40")]
    assert [f["tipo"] for f in aplicar_regla_minimas(d).filas] == ["RUTINA", "RUTINA"]
    # solo OCR con 0,03: minima
    c = [_f(0.03, tipo="ALERTA_TERMICA_OCR", source="OCR")]
    assert aplicar_regla_minimas(c).filas[0]["tipo"] == "RUTINA"


@pytest.mark.parametrize("modo", ["SN", "SE"])
def test_contraejemplo_del_verificador_la_protegida_no_desaparece(modo):
    # verif820/contraej.py: consolidado 0,04 y OCR 1,5 MW en el mismo minuto.
    filas = [_f(0.04, vol="Lascar"), _f(1.5, tipo="ALERTA_TERMICA_OCR", source="OCR", vol="Lascar")]
    out = aplicar_regla_minimas(filas, modo)
    assert pasadas_protegidas(out.filas) == pasadas_protegidas(filas) == {("Lascar", "VIIRS375", "2026-09-10 05:30")}
    assert out.filas == filas and not out.minimas


@pytest.mark.parametrize("modo", ["SN", "SE"])
def test_ventana_de_120_s_entre_minutos_distintos(modo):
    # La misma pasada puede caer en dos minutos (consolidado 05:30:50, OCR 05:31:20). El etiquetador parea a
    # +-120 s, asi que la regla tambien: una alerta por encima del umbral a menos de 120 s impide la minima.
    filas = [_f(0.04, hora="2026-09-10 05:30:50"), _f(1.5, tipo="ALERTA_TERMICA_OCR", source="OCR", hora="2026-09-10 05:31:20")]
    out = aplicar_regla_minimas(filas, modo)
    assert out.filas == filas and not out.minimas
    # a mas de 120 s son pasadas distintas y la minima si cuenta
    lejos = [_f(0.04, hora="2026-09-10 05:30:00"), _f(1.5, tipo="ALERTA_TERMICA_OCR", source="OCR", hora="2026-09-10 05:33:30")]
    assert aplicar_regla_minimas(lejos, modo).minimas == {("Lastarria", "VIIRS375", "2026-09-10 05:30")}


@pytest.mark.parametrize("modo", ["SN", "SE", "original"])
@pytest.mark.parametrize("umbral", [0.04, 0.05])
def test_las_protegidas_nunca_cambian(modo, umbral):
    filas = _filas() + [_f(5.18, tipo="ALERTA_TERMICA_OCR", source="OCR", hora="2026-09-11 05:00:00"),
                        _f(2.27, tipo="FALSO_POSITIVO_OCR", source="OCR", hora="2026-09-11 06:00:00")]
    out = aplicar_regla_minimas(filas, modo, umbral_mw=umbral)
    for lectura in ("A", "B"):
        assert [alerta_protegida(f, lectura=lectura) for f in out.filas] == \
               [alerta_protegida(f, lectura=lectura) for f in filas]


# ------------------------------------------------------------------ efecto en el etiquetador
def _etiquetas(modo):
    import banco_paridad as bp
    from datetime import datetime, timezone
    # una noche de Lastarria en VIIRS 375: una alerta minima de 0,04 a las 05:30 y una RUTINA con VRP 0 a las
    # 07:00 (consolidado). Sin la regla la noche tiene alerta: la RUTINA no es negativo limpio.
    filas = [_f(0.04, hora="2026-09-10 05:30:00"), _f(0.0, tipo="RUTINA", hora="2026-09-10 07:00:00")]
    recs = [{"vol": "Lastarria", "b": "VIIRS375", "dt": datetime(2026, 9, 10, h, m, tzinfo=timezone.utc),
             "noche": "2026-09-10"} for h, m in ((5, 30), (7, 0))]
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, bp._coords_por_volcan(), ("2026-09-10", "2026-09-10"),
                                              regla_minimas=modo)
    bp.etiquetar(recs, por_vb, ns, nv)
    return [r["lab"] for r in recs]


def test_etiquetador_original():
    assert _etiquetas("original") == ["pos", "sin_info"]


def test_etiquetador_sn_la_noche_queda_limpia():
    assert _etiquetas("SN") == ["neg_limpio", "neg_limpio"]


def test_etiquetador_se_estrato_aparte_y_la_noche_no_cambia():
    assert _etiquetas("SE") == ["minima", "sin_info"]


def test_etiquetador_por_defecto_es_la_etiqueta_original():
    # El etiquetador compartido conserva la etiqueta del scraper por defecto para que los resultados ya
    # publicados se reproduzcan tal cual; cada evaluacion nueva pasa el modo y reporta los tres.
    import banco_paridad as bp
    import inspect
    assert inspect.signature(bp.indexar_referencia).parameters["regla_minimas"].default == "original"
