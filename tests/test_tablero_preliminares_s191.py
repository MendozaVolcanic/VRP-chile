# -*- coding: utf-8 -*-
"""S191 (2026-11-20): los 34 volcanes sin MIROVA quedan a la vista como PRELIMINARES, con «paridad no medida».

POR QUÉ. Decisión de Nicolás del 2026-11-20 («Preliminares, rotulados»; N1 y D14 de tasks/DECISIONES_34_S187.md,
opción b). Los 34 están en la página principal junto a los 11 desde #992, pero MIROVA no los publica: no hay con qué
medir su paridad, y nadie revisó todavía si su calor es volcánico (fumarola, lago tibio, campo geotermal). Hasta hoy la
barra «Estado actual» los sumaba en las mismas casillas que a los 11: un punto «Moderado» en un volcán nuevo valía lo
mismo que en Láscar, y la casilla «Sin datos» decía 38 cuando los 11 tenían datos. La tabla de últimas detecciones
tampoco los marcaba. Este cambio es SÓLO de presentación: ningún record, valor ni detección cambia.

QUÉ FIJA, ejecutando en node las funciones reales de frontend/index.html:
- esPreliminar: verdadero sólo para la sombra de los 34.
- contarEstadoTablero: los 11 en las casillas de nivel; los 34 aparte (cuántos con anomalía, de cuántos), sin perder ni
  duplicar volcanes.
- que la página los usa: la barra, la tarjeta, el detalle y la tabla.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría si el código estuviera mal? Cada caso tiene control: un volcán de los
11 nunca es preliminar, uno de los 34 nunca entra a las casillas de nivel, y la suma cuadra. (2) ¿Y si la extracción
muriera? `_fuente` lanza si no encuentra la función y node falla con mensaje si el código no corre.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INDEX = RAIZ / "frontend" / "index.html"
SRC = INDEX.read_text(encoding="utf-8")

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`. Copia de la de test_tablero_absorbe_preliminar34_s183.py."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _node(tmp_path, cuerpo, datos):
    js = "\n".join(_fuente(SRC, n) for n in ("esPreliminar", "contarEstadoTablero"))
    js += "\nconst DATOS = " + json.dumps(datos) + ";\n" + cuerpo
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


ONCE = [{"name": "Lascar", "hasMirova": True}, {"name": "Llaima", "hasMirova": True}]
SOMBRA = [{"name": "Antuco", "hasMirova": False, "fuente": "sombra_34"},
          {"name": "Calbuco", "hasMirova": False, "fuente": "sombra_34"},
          {"name": "Hudson", "hasMirova": False, "fuente": "sombra_34"}]


def test_es_preliminar_solo_la_sombra(tmp_path):
    out = _node(tmp_path, "console.log(JSON.stringify(DATOS.map(v => esPreliminar(v)).concat([esPreliminar(null)])));",
                ONCE + SOMBRA + [{"name": "SinFuente", "hasMirova": False}])
    assert out == [False, False, True, True, True, False, False]


def test_contar_separa_los_34_y_cuadra(tmp_path):
    niveles = {"Lascar": "mod", "Llaima": "nd", "Antuco": "low", "Calbuco": "nd", "Hudson": "vhigh"}
    cuerpo = ("const N = " + json.dumps(niveles) + ";\n"
              "console.log(JSON.stringify(contarEstadoTablero(DATOS, v => N[v.name])));")
    out = _node(tmp_path, cuerpo, ONCE + SOMBRA)
    assert out["principales"] == {"high": 0, "mod": 1, "low": 0, "vlow": 0, "nd": 1}
    assert out["preliminares"] == {"con_anomalia": 2, "total": 3}
    assert sum(out["principales"].values()) + out["preliminares"]["total"] == len(ONCE + SOMBRA)


def test_un_volcan_de_los_34_en_alto_no_sube_la_casilla_alto(tmp_path):
    cuerpo = "console.log(JSON.stringify(contarEstadoTablero(DATOS, v => 'high')));"
    out = _node(tmp_path, cuerpo, ONCE + SOMBRA)
    assert out["principales"]["high"] == 2
    assert out["preliminares"] == {"con_anomalia": 3, "total": 3}


def test_la_pagina_usa_el_rotulo_en_barra_tarjeta_detalle_y_tabla():
    barra = _fuente(SRC, "buildAlertSummary")
    assert re.search(r"\bcontarEstadoTablero\(", barra), "la barra no separa a los 34"
    assert re.search(r"\bROTULO_PRELIMINAR\b|\bTXT_PRELIMINAR\b", barra), "la barra no rotula la casilla de los 34"
    tabla = _fuente(SRC, "buildNRTTable")
    assert re.search(r"\besPreliminar\(det\.volcano\)", tabla), "la tabla no marca las filas de los 34"
    assert re.search(r'tag\.textContent = ROTULO_PRELIMINAR\b', SRC), "la tarjeta no usa el rótulo"
    assert "sin MIROVA · 1 vez al día" not in SRC, "quedó el rótulo viejo de la tarjeta"
    assert "paridad con MIROVA no medida" in _fuente(SRC, "renderDetail"), "el detalle no lo dice"
    m = re.search(r'^const ROTULO_PRELIMINAR = "([^"]+)";', SRC, re.M)
    assert m and "Preliminar" in m.group(1) and "paridad no medida" in m.group(1)
