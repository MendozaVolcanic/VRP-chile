# -*- coding: utf-8 -*-
"""S142: la ventana de falsas publicaciones del auto-audit no cruza el cambio de régimen.

POR QUE: el PR #535 (2026-08-28) apagó la máscara de nube de 260 K. Con la máscara, la nieve fría
de invierno caía como nube, el primer pase quedaba sin fondo y la pasada no podía publicar: esa
ceguera se leía como precisión. Al apagarla, la publicación en negativos limpios de VIIRS 375 pasó
de 62,1 % a 87,1 % (experiments/_s142_linea_base/linea_base_post535.json). Una ventana rodante de
60 días que cruza ese corte mezcla los dos regímenes y el número sube solo, semana a semana, sin
que cambie nada. La ventana de esta métrica empieza en el primer día del régimen vigente (después
de #571, 2026-09-01) mientras los 60 días lo crucen; cuando dejan de cruzarlo vuelve a ser la rodante.

Recall y magnitud conservan su ventana: el cambio de régimen no movió el recall (100 % de 104
pasadas V375 después de #571).
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.auto_audit_weekly import (INICIO_REGIMEN_FALSAS,  # noqa: E402
                                       WINDOW_DAYS, ventana_falsas)


def test_inicio_del_regimen_vigente():
    assert INICIO_REGIMEN_FALSAS == "2026-09-01"


def test_ventana_recortada_mientras_cruza_el_corte():
    assert ventana_falsas(date(2026, 9, 15)) == ("2026-09-01", "2026-09-15")


def test_ventana_rodante_cuando_ya_no_cruza():
    hoy = date(2026, 12, 1)
    assert WINDOW_DAYS == 60
    assert ventana_falsas(hoy) == ("2026-10-02", "2026-12-01")


def test_el_borde_exacto_no_se_recorta():
    # 2026-10-31 menos 60 días es 2026-09-01: coincide con el inicio, no hay recorte que hacer
    assert ventana_falsas(date(2026, 10, 31)) == ("2026-09-01", "2026-10-31")


def test_main_mide_falsas_con_su_ventana_y_la_publica():
    src = (ROOT / "scripts" / "auto_audit_weekly.py").read_text(encoding="utf-8")
    # A92: frontera de palabra, para que un nombre viejo contenido en otro no dé falso verde
    assert re.search(r"(?<![A-Za-z0-9_])medir_falsas_ventana\(\s*win_falsas\s*\)", src)
    assert re.search(r"(?<![A-Za-z0-9_])win_falsas\s*=\s*ventana_falsas\(", src)
    assert re.search(r"[\"']ventana_falsas[\"']\s*:", src)
