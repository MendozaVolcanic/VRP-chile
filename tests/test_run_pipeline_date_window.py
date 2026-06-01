"""TDD S96 — ventana de fechas por defecto del NRT incluye el DÍA EN CURSO.

Bug operacional (decisión Nicolás S95): el default de run_pipeline.py procesaba
`range(7, 0, -1)` = días 7..1 atrás, EXCLUYENDO hoy (día 0). Las pasadas
nocturnas chilenas caen en la madrugada UTC del día en curso y LANCE las publica
~3 h después; procesar solo hasta ayer las perdía por ~24 h → dashboard
sistemáticamente 1 día atrás.

Fix S96: `default_date_window(today)` devuelve hoy (día 0) + 7 días atrás (8
fechas), orden cronológico ascendente. Idempotente vía dedup de store.py.

Estos tests fijan el contrato para que un revert accidental de los límites del
range se detecte.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

_RP_PATH = Path(__file__).parent.parent / "scripts" / "run_pipeline.py"
_spec = importlib.util.spec_from_file_location("run_pipeline_under_test", _RP_PATH)
run_pipeline = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_pipeline)

default_date_window = run_pipeline.default_date_window


def test_incluye_dia_en_curso():
    """El bug S96: hoy (día 0) DEBE estar en la ventana. Es el corazón del fix."""
    today = datetime(2026, 6, 1)
    window = default_date_window(today)
    assert window[-1].date() == today.date(), (
        "El último día de la ventana debe ser HOY (día 0). Si falla, el range "
        "volvió a excluir el día en curso (regresión del fix S96)."
    )


def test_longitud_ocho_dias():
    """hoy + 7 atrás = 8 fechas con lookback default."""
    window = default_date_window(datetime(2026, 6, 1))
    assert len(window) == 8


def test_primer_dia_es_siete_atras():
    today = datetime(2026, 6, 1)
    window = default_date_window(today)
    assert window[0].date() == (today - timedelta(days=7)).date()


def test_orden_cronologico_ascendente():
    """Más viejo primero → el último record persistido es el más reciente."""
    window = default_date_window(datetime(2026, 6, 1))
    assert window == sorted(window)


def test_lookback_personalizado_incluye_hoy():
    today = datetime(2026, 6, 1)
    window = default_date_window(today, lookback_days=2)
    assert len(window) == 3  # hoy + 2 atrás
    assert window[-1].date() == today.date()
    assert window[0].date() == (today - timedelta(days=2)).date()


def test_cruce_de_mes_preserva_offsets():
    """Robustez en borde de mes (hoy=01-jun → primer día 25-may)."""
    today = datetime(2026, 6, 1)
    window = default_date_window(today)
    assert window[0].date() == datetime(2026, 5, 25).date()
    assert window[-1].date() == datetime(2026, 6, 1).date()
