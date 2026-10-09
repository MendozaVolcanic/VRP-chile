# -*- coding: utf-8 -*-
"""S150 - el laboratorio (`experimental`) queda congelado en la deteccion de produccion del 2026-10-09.

POR QUE. La replica va a cambiar para parecerse mas a MIROVA (conectiva max, sin Test 1, banda 22, etiqueta
MODIS desde el cumulo, quizas sin tope D9 ni compuerta D22), y casi todos esos cambios hacen que vea MENOS. El
laboratorio existe para ver lo que MIROVA no publica; como hereda de `mirova_equivalent`, sin valores propios se
arrastraria con la replica (es el defecto de S147 por otra puerta: un laboratorio mas ciego que el producto).

QUE MIDE: (1) hoy el laboratorio resuelve IGUAL que produccion en todo salvo nombre y directorio (no se
introdujo ninguna diferencia por accidente al congelarlo; EL DIA QUE LA REPLICA ADOPTE UN CAMBIO este test cae
a proposito y se reemplaza por la lista de diferencias declaradas entre los dos perfiles); (2) los parametros congelados tienen los valores de
produccion de hoy, resueltos como los resuelve el codigo (VRP_PROFILE, nunca leyendo el YAML: A89).

LAS DOS PREGUNTAS DEL INSTRUMENTO: si alguien borrara un valor congelado y la replica cambiara, el test 2
fallaria (resuelve el valor efectivo); si la resolucion de perfiles fallara, `_resolver` levanta un error y el
test cae en rojo, no en verde.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COD = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) "
       "if k.isupper() and k != 'VALID_PROFILES'}))")
CONGELADOS = {
    "ENABLE_TEST1_PATH": "True",
    "ENABLE_TESTS_23_PROSE_BRANCH": "False",
    "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375": "False",
    "ENABLE_MODIS_B22_PRIMARY": "False",
    "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER": "False",
    "PATH_D_ONLY_CAP_MW": "5.0",
}


def _resolver(nombre):
    out = subprocess.run([sys.executable, "-c", COD], capture_output=True, text=True, cwd=RAIZ,
                         env=dict(os.environ, VRP_PROFILE=nombre, PYTHONIOENCODING="utf-8"), check=True).stdout
    return json.loads([l for l in out.splitlines() if l.startswith("@@")][0][2:])


def test_el_laboratorio_hoy_es_igual_a_produccion_salvo_nombre():
    lab, prod = _resolver("experimental"), _resolver("mirova_equivalent")
    difieren = {k for k in set(lab) | set(prod) if lab.get(k) != prod.get(k)} - {"PROFILE_NAME", "DATA_SUBDIR"}
    assert not difieren, difieren


def test_los_valores_congelados_son_los_de_produccion_del_2026_10_09():
    lab = _resolver("experimental")
    malos = {k: (lab.get(k), v) for k, v in CONGELADOS.items() if lab.get(k) != v}
    assert not malos, malos
