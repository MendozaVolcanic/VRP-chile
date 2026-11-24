# -*- coding: utf-8 -*-
"""S197 (issue #1106): Chaitén MODIS 2026-11-19 02:30 pasa a PERDIDAS_ACEPTADAS, y ninguna otra pasada.

POR QUÉ: la auditoría semanal del 2026-11-23 quedó FUERA DE BANDA por esa alerta protegida de MIROVA (1,07 MW) sin
publicar. El diagnóstico (experiments/_s197_1106/INFORME.md, PR #1107) la explica como un caso de borde: una celda
tibia al suroeste del cráter, una columna fuera de la caja sensible de MODIS y, aun con la caja en el cráter, 0,15 %
bajo el umbral de ETI; categoría física sin atribuir, probablemente transitorio o artefacto. El A/B de la caja
(experiments/_s197_caja_modis/INFORME.md, PR #1108) empató en 330 pasadas. Nicolás decidió aceptarla
(2026-11-24, «Sí, agrégala»). Sin la entrada, el flag volvía cada semana hasta que la pasada saliera de la ventana de
60 días. Control: cualquier otra pasada (otro minuto, otra noche, otro sensor, otro volcán) sigue siendo flag.
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
WIN = ("2026-09-24", "2026-11-23")
CLAVE = ("Chaiten", "MODIS", "2026-11-19 02:30")


def _fila(vol, b, fecha, vrp, dist=None):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": "ALERTA_TERMICA",
            "source": "CONS", "dist_km": dist}


def _brec(vol, b, fecha, pub, sensor):
    dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha[:10], "pub": pub, "sha": "abc", "sensor": sensor}


def _protegidas(filas, recs):
    return aa.alertas_protegidas(filas, recs, WIN, FRONTERA, diurna=lambda *a: False)


def test_chaiten_esta_en_el_registro_con_su_issue_y_sus_informes():
    assert CLAVE in aa.PERDIDAS_ACEPTADAS
    motivo = aa.PERDIDAS_ACEPTADAS[CLAVE]
    assert "#1106" in motivo and "#1107" in motivo and "#1108" in motivo


def test_la_perdida_de_chaiten_no_es_flag_y_se_informa_como_aceptada():
    lista = _protegidas([_fila("Chaiten", "MODIS", "2026-11-19 02:30:00", 1.07, dist=3.61)],
                        [_brec("Chaiten", "MODIS", "2026-11-19 02:30", False, "MODIS_TERRA")])
    assert [(p["estado"], p["perdida_aceptada"]) for p in lista] == [("sin_publicar", True)]
    assert aa.flags_protegidas(lista, "K") == []
    aparte = aa.protegidas_aparte(lista, "K")
    assert len(aparte) == 1
    assert "pérdida aceptada" in aparte[0] and "Chaiten MODIS 2026-11-19 02:30" in aparte[0]


@pytest.mark.parametrize("vol,b,fecha,sensor", [
    ("Chaiten", "MODIS", "2026-11-19 08:25:00", "MODIS_AQUA"),          # otra pasada de esa noche
    ("Chaiten", "MODIS", "2026-11-20 02:30:00", "MODIS_TERRA"),         # otra noche, misma hora
    ("Chaiten", "VIIRS375", "2026-11-19 02:30:00", "VIIRS_NOAA21"),     # mismo minuto, otro sensor
    ("Villarrica", "MODIS", "2026-11-19 02:30:00", "MODIS_TERRA"),      # mismo minuto, otro volcán
])
def test_el_registro_no_acepta_ninguna_otra_pasada_de_chaiten(vol, b, fecha, sensor):
    lista = _protegidas([_fila(vol, b, fecha, 1.5)], [_brec(vol, b, fecha[:16], False, sensor)])
    assert lista[0]["perdida_aceptada"] is False
    assert len(aa.flags_protegidas(lista, "K")) == 1
    assert aa.protegidas_aparte(lista, "K") == []
