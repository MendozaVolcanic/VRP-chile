# S119: en Windows la consola default es cp1252; los mensajes runtime del pipeline
# (ej. _diag del breaker CMR en pipeline/fetch.py con "→") crashean con
# UnicodeEncodeError cuando la suite corre con -s (workaround S96) y un test
# ejercita ese path. En GH Actions (Linux, utf-8) no pasa. Reconfigurar stdout/err
# a utf-8 acá blinda la suite local sin tocar pipeline/ (A45).
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


# S149: ningun test deja el perfil cambiado para el que viene despues.
#
# POR QUE. `pipeline.profile` resuelve el perfil UNA vez, al importarse, leyendo VRP_PROFILE. Los tests
# que prueban un perfil de A/B lo hacen cambiando la variable y recargando el modulo, y 22 de ellos no
# lo devolvian a su estado (medido con un detector sobre la suite completa: 22 fugas, varias dejando
# ademas la variable de entorno cambiada). El test siguiente que leia `pipeline.profile` recibia los
# flags de un brazo de A/B en vez de los operacionales. La suite completa pasaba por el ORDEN en que
# corre; un subconjunto (`-k "profile or guard"`) hacia fallar
# test_probe_3brazos_s136::test_el_brazo_actual_refleja_el_perfil_operacional, que pasaba solo. Un test
# que pasa o falla segun quien corrio antes no mide lo que dice medir (misma familia que A112).
#
# QUE HACE. Despues de cada test, si la variable o el perfil cargado no son los de antes del test, los
# restaura y recarga el modulo. No cambia lo que ningun test ve DURANTE su corrida.
# LIMITE, declarado: solo restaura `pipeline.profile` y VRP_PROFILE. Un modulo que hizo
# `from pipeline.profile import X` y fue recargado bajo otro perfil conserva sus copias.
import importlib  # noqa: E402
import os  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _perfil_no_se_fuga_entre_tests():
    env_antes = os.environ.get("VRP_PROFILE")
    prof = sys.modules.get("pipeline.profile")
    nombre_antes = getattr(prof, "PROFILE_NAME", None)
    yield
    if os.environ.get("VRP_PROFILE") != env_antes:
        if env_antes is None:
            os.environ.pop("VRP_PROFILE", None)
        else:
            os.environ["VRP_PROFILE"] = env_antes
    prof = sys.modules.get("pipeline.profile")
    if prof is not None and nombre_antes is not None and prof.PROFILE_NAME != nombre_antes:
        importlib.reload(prof)
