"""S159, tarea I3 (parte mecánica): una sola ventana de pareo con MIROVA en los scripts de producción.

POR QUE. La segunda ronda de S158 encontró cuatro definiciones de «alerta de MIROVA» con pareos de 20, 8 y 5 minutos
y de minuto exacto (experiments/_s158_audit_r2/m1/INFORME.md, H8). En los scripts que producen números publicados el
pareo es uno solo, ±120 s, pero vivía escrito DOS veces como literal: `banco_paridad.TOL_S = 120` y
`clase_mirova.VENTANA_S = 120`, con un comentario que decía que eran la misma. Dos literales que «son la misma» se
separan el día que alguien cambia uno. Ahora la ventana se define una vez, en clase_mirova.VENTANA_S, y los demás la
importan. No cambia ningún número: el valor sigue siendo 120 s.
La unificación de QUÉ es una alerta (prefijo «ALERTA» contra la lista TIPOS_ALERTA) no es mecánica y queda propuesta
en experiments/_s159/instrumentos/NOTAS.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

PRODUCCION = ("banco_paridad.py", "clase_mirova.py", "auto_audit_weekly.py", "vigilancia_sombra.py")
LITERAL = re.compile(r"^(TOL_S|TOL_PASADA_S|VENTANA_S)\s*=\s*\d", re.M)


def test_la_ventana_de_pareo_se_escribe_una_sola_vez():
    con_literal = [n for n in PRODUCCION if LITERAL.search((RAIZ / "scripts" / n).read_text(encoding="utf-8"))]
    assert con_literal == ["clase_mirova.py"], "ventana de pareo escrita como literal en: %s" % con_literal


def test_los_pareos_de_produccion_son_el_mismo_valor():
    import banco_paridad as bp
    import clase_mirova as cm
    assert cm.VENTANA_S == 120          # el número no cambia
    assert bp.TOL_S == cm.VENTANA_S
