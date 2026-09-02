# -*- coding: utf-8 -*-
"""S132 R14 — `volcanoes.yaml` es la fuente de verdad de la región de cada volcán.

POR QUÉ ESTE GUARD Y NO UN BUILD. El frontend es estático: cada vista lleva su propia copia
del arreglo de volcanes escrita a mano en el HTML. Esa duplicación ya produjo un bug real
—Lastarria aparecía en «Atacama» y Tupungatito en «Valparaíso» en `index` y `mosaico`,
mientras `diario` los tenía bien—, que S131 arregló caso por caso. Arreglar los dos casos
no elimina la clase de bug: el tercero aparece la próxima vez que alguien agregue un volcán
a una vista y no a las otras.

Montar un paso de build que genere el JS desde el YAML sería la solución completa, pero
agrega infraestructura y un artefacto generado al repo. Este guard consigue lo mismo que
importa —que las tres vistas no puedan divergir de la fuente de verdad sin que alguien se
entere— derivando la comparación del código, sin fijar ninguna lista a mano (regla B de los
guards S131).

Un volcán que exista en una vista y no en `volcanoes.yaml` también es un error: la vista
estaría publicando un volcán que el pipeline no conoce.
"""
import os
import re

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VISTAS = ["frontend/index.html", "frontend/diario.html", "frontend/mosaico.html"]


def _regiones_yaml():
    with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as fp:
        y = yaml.safe_load(fp)
    return {v["name"]: v.get("region") for v in y["volcanoes"]}


def _regiones_vista(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fp:
        s = fp.read()
    return {m.group(1): m.group(2)
            for m in re.finditer(r'name:\s*"([^"]+)"[^\n]*?region:\s*"([^"]+)"', s)}


def test_todo_volcan_del_yaml_tiene_region():
    sin = [n for n, r in _regiones_yaml().items() if not r]
    assert not sin, f"volcanes sin `region` en volcanoes.yaml: {sin}"


@pytest.mark.parametrize("vista", VISTAS)
def test_la_vista_no_diverge_del_yaml(vista):
    yaml_reg = _regiones_yaml()
    vista_reg = _regiones_vista(vista)
    assert vista_reg, f"no encontré ningún volcán con región en {vista}"

    desconocidos = sorted(set(vista_reg) - set(yaml_reg))
    assert not desconocidos, (
        f"{vista} publica volcanes que no están en volcanoes.yaml: {desconocidos}")

    mal = {n: (vista_reg[n], yaml_reg[n]) for n in vista_reg if vista_reg[n] != yaml_reg[n]}
    assert not mal, (
        f"{vista} discrepa de volcanoes.yaml (vista, yaml): {mal}. "
        "La fuente de verdad es el yaml; corregir la vista, no el yaml, salvo que el yaml "
        "sea el equivocado.")
