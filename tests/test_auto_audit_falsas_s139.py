# -*- coding: utf-8 -*-
"""Fase 0 tarea 6 (S139/S140): el auto-audit semanal mide falsas publicaciones, sin alarma.

POR QUE: la brecha con MIROVA es sobre-publicacion (S139) y el auto-audit solo medía recall y
magnitud. Ahora publica, por sensor y por régimen, el porcentaje de pasadas negativas limpias en que
el dashboard publica, con la banda de terminado de la spec §2 al lado (10 % focales, 15 % nevados).

DECISION de Nicolas (2026-09-14): medir SIN alarma. Hoy V375 esta en ~64 %; con flag, el workflow
abriria un issue cada lunes hasta cerrar la Fase 1 y taparia las regresiones reales. Por eso este
test exige tambien que la metrica nunca agregue flags.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.auto_audit_weekly import (FALSAS_BANDA_TERMINADO,  # noqa: E402
                                       resumir_falsas)


def _rec(vol, b, lab, pub):
    return {"vol": vol, "b": b, "lab": lab, "pub": pub, "neg_estricto": False,
            "noche": "2026-09-01"}


def test_porcentaje_y_sin_flag():
    recs = [_rec("Lascar", "VIIRS375", "neg_limpio", 1),
            _rec("Lascar", "VIIRS375", "neg_limpio", 0),
            _rec("Lascar", "VIIRS375", "pos", 1),
            _rec("Lascar", "VIIRS375", "sin_info", 1)]
    flags = ["recall MODIS 90% < banda 95%"]
    antes = list(flags)
    res = resumir_falsas(recs, flags)
    v = res["por_sensor"]["VIIRS375"]
    assert v["falsas_pub_pct"] == 50.0
    assert v["n_neg_limpio"] == 2
    assert res["por_regimen"]["focal"]["VIIRS375"]["falsas_pub_pct"] == 50.0
    assert res["por_regimen"]["focal"]["VIIRS375"]["banda_terminado_pct"] == 10.0
    assert res["por_regimen"]["focal"]["VIIRS375"]["sobre_banda_terminado"] is True
    # decision S140: medir sin alarma
    assert flags == antes
    assert res["alarma"] is False


def test_nevado_usa_su_banda_y_sin_negativos_da_none():
    recs = [_rec("Villarrica", "MODIS", "neg_limpio", 0),
            _rec("Villarrica", "MODIS", "neg_limpio", 0)]
    res = resumir_falsas(recs, [])
    n = res["por_regimen"]["nevado"]["MODIS"]
    assert n["falsas_pub_pct"] == 0.0 and n["banda_terminado_pct"] == 15.0
    assert n["sobre_banda_terminado"] is False
    assert res["por_sensor"]["VIIRS750"]["falsas_pub_pct"] is None


def test_bandas_de_la_spec():
    assert FALSAS_BANDA_TERMINADO == {"focal": 10.0, "nevado": 15.0}
