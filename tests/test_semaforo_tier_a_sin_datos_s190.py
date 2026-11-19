# -*- coding: utf-8 -*-
"""S190 (auditoría de Codex, ronda 2, F6-113, CONFIRMADO gravedad 3 por el verificador Claude del frente 6,
D:\\codex-vrp\\_salida\\ronda2\\f6_verificacion\\VEREDICTO.md): el semáforo del encabezado del tablero decía «Sistema
Operativo» con un volcán principal sin ningún dato cargado.

POR QUÉ: `trackHeaderFreshness` (frontend/index.html) toma la peor frescura de los 11 Tier A, pero descartaba la clase
`mon-none` («sin datos en este tablero»), que es lo que sale cuando el JSON del volcán no carga o viene vacío. Con 10
volcanes al día y uno sin datos, el encabezado quedaba en verde; con los 11 sin datos, quedaba el texto fijo del HTML,
también «Sistema Operativo». La tarjeta del volcán sí avisaba, pero el operador que mira el encabezado no.

Se prueba el bloque tal como se publica: se extrae de index.html y se corre en node con un DOM falso. Si node no está,
la prueba se salta (como las demás del tablero).
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
HTML = RAIZ / "frontend" / "index.html"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el tablero se prueba con node")

DOM_FALSO = """
const _dot = {className: "status-dot"}, _txt = {textContent: "Sistema Operativo", title: ""};
const document = {querySelector: (s) => s === ".status-dot" ? _dot : null,
                  getElementById: (i) => i === "status-text" ? _txt : null};
"""


def _bloque():
    t = HTML.read_text(encoding="utf-8")
    i = t.index("const _FRESH_RANK")
    j = t.index("// S137 D5", i)
    return t[i:j]


def semaforo(clases):
    frescos = [{"cls": c, "txt": c} for c in clases]
    js = (DOM_FALSO + _bloque() + "\nfor (const f of %s) trackHeaderFreshness(f);\n"
          "process.stdout.write(JSON.stringify([_dot.className, _txt.textContent]));") % json.dumps(frescos)
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_un_tier_a_sin_datos_no_deja_sistema_operativo():
    dot, txt = semaforo(["mon-fresh"] * 10 + ["mon-none"])
    assert txt != "Sistema Operativo", (dot, txt)
    assert "mon-none" in dot


def test_once_tier_a_sin_datos_no_deja_sistema_operativo():
    dot, txt = semaforo(["mon-none"] * 11)
    assert txt != "Sistema Operativo", (dot, txt)


def test_sin_datos_pesa_mas_que_sin_pasadas_recientes():
    _, txt = semaforo(["mon-stale", "mon-none", "mon-fresh"])
    _, txt_inverso = semaforo(["mon-none", "mon-stale"])
    assert txt == txt_inverso
    assert re.search(r"sin datos", txt, re.I), txt


def test_control_once_al_dia_es_sistema_operativo():
    assert semaforo(["mon-fresh"] * 11) == ["status-dot mon-fresh", "Sistema Operativo"]


def test_control_uno_viejo_es_sin_pasadas_recientes():
    assert semaforo(["mon-fresh"] * 10 + ["mon-stale"])[1] == "Sin pasadas recientes"


def test_el_punto_sin_datos_tiene_estilo_propio():
    """Sin regla CSS el punto quedaría con el verde pulsante por defecto de .status-dot."""
    assert re.search(r"\.status-dot\.mon-none\s*\{", HTML.read_text(encoding="utf-8"))
