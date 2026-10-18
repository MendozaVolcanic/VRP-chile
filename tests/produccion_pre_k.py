# -*- coding: utf-8 -*-
"""S153: la produccion de ANTES de adoptar K, como ancla para los tests que se escribieron sobre ella.

POR QUE. En S153 la replica adopto K (regla experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md, #848): Test 1
integrado apagado, conectiva `max` de los Tests 2 y 3 y banda 22 primaria en MODIS. Varios tests fijan una
propiedad del CODIGO medida sobre la deteccion de entonces: el golden bit a bit de S142 («los flags D22 y D25
apagados no cambian nada»), las pruebas sinteticas de las sondas MxD03 (escenas con la rama del Test 1) y la
calibracion de la vara diurna (2 K y 6 K, medida con `min`). Regenerarlos con K no protegeria lo mismo: el
golden dejaria de comparar contra el codigo previo y las escenas del Test 1 dejarian de ejercer esa rama, que
sigue viva en el laboratorio y en los brazos historicos. Lo correcto es correrlos sobre la deteccion que
midieron, y esa deteccion tiene nombre: el perfil congelado `_s146_ab_control` («produccion (C0)»).

DOS FORMAS, segun como corre el test.
- En subproceso (el arnes de S142): `VRP_PROFILE=PERFIL`.
- En el mismo proceso: los procesadores copian los flags al importarse (`from pipeline.profile import ...`),
  asi que cambiar la variable no llega (A89). `produccion_pre_k()` parchea esas copias, en los tres
  procesadores, con los valores que RESUELVE el perfil ancla.

LA PROTECCION CONTRA LA DERIVA (A117). `valores()` resuelve el ancla y la produccion con pipeline.profile en
procesos limpios y exige que difieran EXACTAMENTE en los tres flags de K. Si mañana la produccion adopta otro
cambio, o alguien toca el ancla, el parche ya no reproduce el ancla y todo test que lo use cae con un mensaje
que lo dice, en vez de medir otra cosa en silencio.
"""
import ast
import importlib
import json
import os
import subprocess
import sys
from contextlib import ExitStack, contextmanager
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PERFIL = "_s146_ab_control"
FLAGS_K = ("ENABLE_TEST1_PATH", "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY")
PROCESADORES = ("pipeline.process_modis", "pipeline.process_viirs", "pipeline.process_viirs_mod")
_COD = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) "
        "if k.isupper() and k != 'VALID_PROFILES'}))")


@lru_cache(maxsize=None)
def resolver(nombre):
    """Constantes de pipeline.profile resueltas para `nombre` en un proceso limpio (nunca leyendo el YAML)."""
    out = subprocess.run([sys.executable, "-c", _COD], capture_output=True, text=True, cwd=ROOT,
                         env=dict(os.environ, VRP_PROFILE=nombre, PYTHONIOENCODING="utf-8"), check=True).stdout
    return json.loads([l for l in out.splitlines() if l.startswith("@@")][0][2:])


def valores():
    ancla, prod = resolver(PERFIL), resolver("mirova_equivalent")
    difieren = {k for k in set(ancla) | set(prod) if ancla.get(k) != prod.get(k)} - {"PROFILE_NAME", "DATA_SUBDIR"}
    assert difieren == set(FLAGS_K), (
        f"el ancla {PERFIL} ya no es «produccion menos K»: difiere de mirova_equivalent en {sorted(difieren)}. "
        "Si la produccion adopto otro cambio, decidir si estos tests lo heredan antes de tocar FLAGS_K")
    return {k: ast.literal_eval(ancla[k]) for k in FLAGS_K}


@contextmanager
def produccion_pre_k():
    """Corre lo de adentro con los procesadores en la deteccion de antes de K (la del ancla)."""
    vals = valores()
    with ExitStack() as pila:
        for nombre in PROCESADORES + ("pipeline.profile",):
            mod = importlib.import_module(nombre)
            for k, v in vals.items():
                if hasattr(mod, k):
                    pila.enter_context(patch.object(mod, k, v))
        yield vals
