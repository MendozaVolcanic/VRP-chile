# -*- coding: utf-8 -*-
"""S153 - adopcion de K en la replica (regla experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md, PR #848).

POR QUE. K (sin el Test 1 integrado, conectiva `max` de Coppola 2016a, banda 22 primaria en MODIS) cumplio la
regla aprobada por Nicolas antes de evaluar V2: no pierde ninguna alerta protegida y baja la publicacion donde MIROVA
no vio nada de 85 a 4 % en VIIRS 375 (experiments/_s153_fk_v2/). Este guard fija los tres flags tal como los resuelve
el codigo (VRP_PROFILE, nunca el YAML: A89), para que una edicion suelta del perfil no revierta la adopcion sin
pasar por el tag pre-s153-adopcion-k y un git revert.

Y fija la diferencia DECLARADA con el laboratorio: `experimental` quedo congelado en la deteccion del 2026-10-09
(S150, #771) y hace de sombra de la adopcion (regla §4.9), asi que difiere de produccion exactamente en estos tres
flags, ni uno mas ni uno menos.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COD = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: repr(getattr(p, k)) for k in dir(p) "
       "if k.isupper() and k != 'VALID_PROFILES'}))")
K = {"ENABLE_TEST1_PATH": "False", "ENABLE_TESTS_23_PROSE_BRANCH": "True", "ENABLE_MODIS_B22_PRIMARY": "True"}


def _resolver(nombre):
    out = subprocess.run([sys.executable, "-c", COD], capture_output=True, text=True, cwd=RAIZ,
                         env=dict(os.environ, VRP_PROFILE=nombre, PYTHONIOENCODING="utf-8"), check=True).stdout
    return json.loads([l for l in out.splitlines() if l.startswith("@@")][0][2:])


def test_produccion_resuelve_los_tres_flags_de_k():
    prod = _resolver("mirova_equivalent")
    malos = {k: (prod.get(k), v) for k, v in K.items() if prod.get(k) != v}
    assert not malos, malos


def test_el_brazo_k_del_ab_y_produccion_son_la_misma_deteccion():
    """El perfil adoptado es el mismo que se midio (brazo _s149_ab_sin_test1_b22_max), salvo nombre y directorio."""
    brazo, prod = _resolver("_s149_ab_sin_test1_b22_max"), _resolver("mirova_equivalent")
    difieren = {k for k in set(brazo) | set(prod) if brazo.get(k) != prod.get(k)} - {"PROFILE_NAME", "DATA_SUBDIR"}
    assert not difieren, difieren


def test_el_laboratorio_difiere_de_produccion_exactamente_en_k():
    lab, prod = _resolver("experimental"), _resolver("mirova_equivalent")
    difieren = {k for k in set(lab) | set(prod) if lab.get(k) != prod.get(k)} - {"PROFILE_NAME", "DATA_SUBDIR"}
    assert difieren == set(K), difieren
