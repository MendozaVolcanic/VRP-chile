# -*- coding: utf-8 -*-
"""Pendiente (i) de la tarea 0.1 del loop: el auto-audit semanal tiene que ver las alertas recuperadas.

POR QUE: desde #778 la referencia unificada suma las filas que el consolidado remoto de Mirova-v1 perdio en
silencio (40 ALERTA_TERMICA). La parte de publicacion del auto-audit ya la usa, pero el paso 1 (las noches con
alerta de MIROVA que fijan el recall) cargaba solo el snapshot crudo: una alerta perdida en el remoto no
contaba como alerta, y su pasada no podia contar como acierto ni como perdida.
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

import auto_audit_weekly as aw  # noqa: E402

CAMPOS = ["timestamp", "Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro",
          "Clasificacion Mirova"]


def _csv(path, filas):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)


def _fila(fecha, tipo="ALERTA_TERMICA", vrp="0.5"):
    return {"timestamp": "", "Fecha_Satelite_UTC": fecha, "Volcan": "Lascar", "Sensor": "VIIRS375", "VRP_MW": vrp,
            "Distancia_km": "1.0", "Tipo_Registro": tipo, "Clasificacion Mirova": "Muy Bajo"}


def test_las_alertas_de_la_union_historica_entran(tmp_path):
    cons, ocr, hist = tmp_path / "c.csv", tmp_path / "o.csv", tmp_path / "h.csv"
    _csv(cons, [_fila("2026-09-10 05:00:00")])
    _csv(ocr, [])
    _csv(hist, [_fila("2026-09-11 05:00:00"), _fila("2026-09-12 05:00:00", tipo="RUTINA", vrp="0")])
    al = aw.alertas_mirova(str(cons), str(ocr), str(hist))
    fechas = sorted(a["fecha_utc"][:16] for a in al)
    assert fechas == ["2026-09-10 05:00", "2026-09-11 05:00"], fechas


def test_la_principal_gana_y_no_duplica(tmp_path):
    cons, ocr, hist = tmp_path / "c.csv", tmp_path / "o.csv", tmp_path / "h.csv"
    _csv(cons, [_fila("2026-09-10 05:00:00", vrp="0.9")])
    _csv(ocr, [])
    _csv(hist, [_fila("2026-09-10 05:00:00", vrp="0.1")])
    al = aw.alertas_mirova(str(cons), str(ocr), str(hist))
    assert len(al) == 1 and abs(al[0]["vrp_mw"] - 0.9) < 1e-9


def test_control_sin_historico_la_alerta_no_esta(tmp_path):
    cons, ocr, hist = tmp_path / "c.csv", tmp_path / "o.csv", tmp_path / "h.csv"
    _csv(cons, [])
    _csv(ocr, [])
    _csv(hist, [_fila("2026-09-11 05:00:00")])
    assert aw.alertas_mirova(str(cons), str(ocr), None) == []
    assert len(aw.alertas_mirova(str(cons), str(ocr), str(hist))) == 1


def test_por_defecto_usa_la_union_del_repo():
    from referencia_mirova_unificada import HISTORICO_RECUPERADAS
    assert aw.HISTORICO == str(HISTORICO_RECUPERADAS)
