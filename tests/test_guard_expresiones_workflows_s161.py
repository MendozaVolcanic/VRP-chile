# -*- coding: utf-8 -*-
"""S161: ninguna expresión de GitHub Actions usa comillas dobles para un texto.

POR QUÉ: en las expresiones de GitHub Actions (los `if:` y lo que va entre `${{ }}`) un texto literal va entre
comillas SIMPLES; las dobles no existen en esa gramática. Un `if: x == "1"` no da un error al escribirlo: GitHub
rechaza el archivo entero, cada push queda con una corrida en rojo que nadie mira, y el calendario del workflow
nunca dispara. Así quedó `vigilar-osf-mirova.yml` desde S158 (`79aeb3406`): 40 corridas por push en `failure` y 0
por calendario al 2026-10-23, o sea que el vigilante del código de MIROVA en OSF nunca corrió en `main`.

La guarda no reemplaza al parser de GitHub: busca esta forma concreta de romperlo, que ya pasó. Las comillas dobles
alrededor de `${{ }}` dentro de un `run:` (`"${{ steps.x.outputs.y }}"`) son del shell y no cuentan: se mira sólo
lo que queda DENTRO de la expresión.
"""
import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((RAIZ / ".github" / "workflows").glob("*.yml")) + sorted(
    (RAIZ / ".github" / "workflows").glob("*.yaml"))
EXPR = re.compile(r"\$\{\{(.*?)\}\}", re.S)


def _ifs(nodo, ruta=""):
    """Todos los valores de una clave `if` (de job o de paso), con su ruta, recorriendo el YAML ya leído."""
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k == "if" and isinstance(v, str):
                yield ruta + "/if", v
            yield from _ifs(v, "%s/%s" % (ruta, k))
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            yield from _ifs(v, "%s[%d]" % (ruta, i))


def _expresiones(texto):
    """Las expresiones de un archivo: cada `if` (entero si no trae `${{ }}`) y cada `${{ }}` del texto crudo."""
    datos = yaml.safe_load(texto) or {}
    for ruta, v in _ifs(datos):
        dentro = EXPR.findall(v)
        for e in dentro or [v]:
            yield ruta, e
    for m in EXPR.finditer(texto):
        yield "l. %d" % (texto.count("\n", 0, m.start()) + 1), m.group(1)


TEXTO_SIMPLE = re.compile(r"'(?:[^']|'')*'")      # un texto literal de la expresión ('' es la comilla escapada)


def violaciones(texto):
    # POR QUÉ quitar antes los textos entre comillas simples: dentro de ellos una comilla doble es un carácter
    # más y es válida (nrt.yml arma un JSON así: fromJson('["Lascar", ...]')). Sólo cuenta la que queda fuera.
    return [(donde, e.strip()) for donde, e in _expresiones(texto) if '"' in TEXTO_SIMPLE.sub("''", e)]


def test_hay_workflows():
    # control: si la ruta estuviera mal, la guarda de abajo pasaría sin mirar nada
    assert len(WORKFLOWS) >= 10, WORKFLOWS


def test_el_detector_ve_la_forma_rota():
    # control positivo: la forma exacta que tenía vigilar-osf-mirova.yml en main antes de S161
    roto = ('"on":\n  workflow_dispatch:\njobs:\n  a:\n    runs-on: ubuntu-24.04\n    steps:\n'
            '      - if: steps.v.outputs.codigo == "1" || steps.v.outputs.codigo == "2"\n        run: echo\n')
    assert violaciones(roto), "el detector no ve comillas dobles en un if"
    sano = roto.replace('"1"', "'1'").replace('"2"', "'2'")
    assert not violaciones(sano), violaciones(sano)
    # las comillas del shell alrededor de ${{ }} no son de la expresión
    shell = '"on":\n  workflow_dispatch:\njobs:\n  a:\n    steps:\n      - run: echo "${{ steps.v.outputs.c }}"\n'
    assert not violaciones(shell), violaciones(shell)
    # comillas dobles DENTRO de un texto entre simples son válidas (la forma de nrt.yml)
    json_ = ('"on":\n  workflow_dispatch:\njobs:\n  a:\n    steps:\n'
             "      - if: contains(fromJson('[\"Lascar\",\"Villarrica\"]'), matrix.volcano) && x != 'it''s'\n"
             "        run: echo\n")
    assert not violaciones(json_), violaciones(json_)


def test_ninguna_expresion_usa_comillas_dobles():
    malas = {}
    for w in WORKFLOWS:
        v = violaciones(w.read_text(encoding="utf-8"))
        if v:
            malas[w.name] = v
    assert not malas, "expresiones con comillas dobles (GitHub rechaza el archivo entero): %s" % malas
