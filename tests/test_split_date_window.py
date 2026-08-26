# -*- coding: utf-8 -*-
"""Tests del partidor de ventanas (scripts/split_date_window.py).

La propiedad que importa: los trozos deben COBERTURAR la ventana entera, sin
huecos y sin solapes. Un hueco = días que nadie procesa (falso negativo
silencioso en la serie); un solape = trabajo repetido y records en disputa.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.split_date_window import split_window  # noqa: E402


def _dias(trozos):
    """Todos los días cubiertos, en orden, con repeticiones si las hay."""
    out = []
    for t in trozos:
        d, fin = date.fromisoformat(t["start"]), date.fromisoformat(t["end"])
        while d <= fin:
            out.append(d)
            d += timedelta(days=1)
    return out


@pytest.mark.parametrize("start,end,max_days", [
    ("2026-04-01", "2026-08-24", 37),   # el caso real del A/B Villarrica
    ("2026-04-01", "2026-04-01", 37),   # un solo día
    ("2026-01-01", "2026-03-01", 1),    # trozos de un día
    ("2026-02-01", "2026-03-05", 40),   # ventana menor que el trozo
    ("2024-02-01", "2024-03-05", 10),   # cruza un 29 de febrero
])
def test_cobertura_exacta_sin_huecos_ni_solapes(start, end, max_days):
    trozos = split_window(start, end, max_days)
    dias = _dias(trozos)

    esperado = []
    d, fin = date.fromisoformat(start), date.fromisoformat(end)
    while d <= fin:
        esperado.append(d)
        d += timedelta(days=1)

    assert dias == esperado, "los trozos deben cubrir la ventana exactamente"
    assert len(dias) == len(set(dias)), "ningún día puede repetirse"


def test_ningun_trozo_excede_el_presupuesto(tmp_path=None):
    trozos = split_window("2026-04-01", "2026-08-24", 37)
    for t in trozos:
        largo = (date.fromisoformat(t["end"])
                 - date.fromisoformat(t["start"])).days + 1
        assert largo <= 37


def test_indices_correlativos_desde_uno():
    trozos = split_window("2026-04-01", "2026-08-24", 37)
    assert [t["idx"] for t in trozos] == list(range(1, len(trozos) + 1))


def test_ventana_del_ab_villarrica_entra_en_cuatro_trozos():
    """146 días / 37 = 4 trozos de ~1 h 40 min cada uno, con margen sobrado."""
    trozos = split_window("2026-04-01", "2026-08-24", 37)
    assert len(trozos) == 4
    assert trozos[0]["start"] == "2026-04-01"
    assert trozos[-1]["end"] == "2026-08-24"


def test_ventana_invertida_falla_fuerte():
    with pytest.raises(ValueError, match="invertida"):
        split_window("2026-08-24", "2026-04-01", 37)


def test_max_days_invalido_falla_fuerte():
    with pytest.raises(ValueError):
        split_window("2026-04-01", "2026-08-24", 0)
