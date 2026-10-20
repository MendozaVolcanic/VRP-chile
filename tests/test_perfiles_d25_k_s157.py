# -*- coding: utf-8 -*-
"""S157 (tarea 1.29): los brazos del A/B de D25 sobre K difieren sólo en lo que declaran.

POR QUÉ. El A/B mide D25 (fondo por vecinos, docs/MIROVA_DIVERGENCES.md) sobre la réplica K. Si el control no es
producción, o si el brazo cambia algo más que la palanca, el A/B mide otra cosa sin dar error (A117). Se comprueba
resolviendo todas las constantes de `pipeline.profile` (nunca el YAML, A89), igual que
tests/test_perfiles_diurno_k_s154.py. El pre-registro es experiments/_s157_prereg_d25/PREREGISTRO.md.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTROL, GEMELO, ON, ON_H1 = ("_s157_ab_d25_k_control", "_s157_ab_d25_k_gemelo", "_s157_ab_d25_k_on",
                              "_s157_ab_d25_k_on_h1")
TODOS = (CONTROL, GEMELO, ON, ON_H1)
NOMBRE = {"PROFILE_NAME", "DATA_SUBDIR"}
D25 = {"ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375", "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750"}

_RESOLVER = """
import importlib, json, os, sys
out = {}
for n in sys.argv[1:]:
    os.environ["VRP_PROFILE"] = n
    import pipeline.profile as p
    p = importlib.reload(p)
    out[n] = {k: repr(getattr(p, k)) for k in dir(p) if k.isupper()}
print("@@" + json.dumps(out))
"""


def _resolver(*nombres):
    r = subprocess.run([sys.executable, "-c", _RESOLVER, *nombres], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    return json.loads([l for l in r.stdout.splitlines() if l.startswith("@@")][0][2:])


def _distintos(a, b):
    return {k for k in set(a) | set(b) if a.get(k) != b.get(k)}


def test_cada_perfil_escribe_en_su_propio_directorio():
    for n in TODOS:
        cfg = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{n}.yaml").read_text(encoding="utf-8"))
        assert cfg["extends"] == "mirova_equivalent"
        assert cfg["output"]["data_subdir"] == n   # el workflow exige DATA_SUBDIR == PROFILE_NAME


def test_los_brazos_difieren_solo_en_lo_declarado():
    res = _resolver("mirova_equivalent", *TODOS)
    prod, c, g, on, h1 = (res[n] for n in ("mirova_equivalent",) + TODOS)
    assert len(prod) > 100   # el instrumento ve las constantes de verdad
    # control = producción salvo nombre, directorio y MODIS apagado (D25 no existe en MODIS)
    assert _distintos(prod, c) == NOMBRE | {"SENSOR_MODIS"}, sorted(_distintos(prod, c))
    assert (prod["SENSOR_MODIS"], c["SENSOR_MODIS"]) == ("True", "False")
    assert _distintos(c, g) == NOMBRE, sorted(_distintos(c, g))
    assert _distintos(c, on) == NOMBRE | D25, sorted(_distintos(c, on))
    assert _distintos(on, h1) == NOMBRE | {"VRP_BG_NEIGHBOR_MAX_HALF_PX"}, sorted(_distintos(on, h1))
    assert (on["VRP_BG_NEIGHBOR_MAX_HALF_PX"], h1["VRP_BG_NEIGHBOR_MAX_HALF_PX"]) == ("3", "1")
    for x in (c, g):
        assert all(x[k] == "False" for k in D25)
    for x in (on, h1):
        assert all(x[k] == "True" for k in D25)
    # la base es K (S153, #850): sin Test 1 integrado, conectiva max, banda 22 MODIS; VIIRS encendido
    for x in (c, g, on, h1):
        assert (x["ENABLE_TEST1_PATH"], x["ENABLE_TESTS_23_PROSE_BRANCH"], x["ENABLE_MODIS_B22_PRIMARY"]) == \
            ("False", "True", "True")
        assert (x["SENSOR_VIIRS_375"], x["SENSOR_VIIRS_750"]) == ("True", "True")


def test_el_workflow_de_reproceso_registra_los_flags_de_d25():
    """A118: el cableado de cada job se lee en su línea FLAGS_BRAZO; sin los flags de D25 ahí, un brazo que no los
    leyó pasaría el control de cableado."""
    src = (ROOT / ".github" / "workflows" / "reproc-s146-ab-sin-test1.yml").read_text(encoding="utf-8")
    linea = [l for l in src.splitlines() if "FLAGS_BRAZO" in l and "json.dumps" in l][0]
    for k in sorted(D25) + ["VRP_BG_NEIGHBOR_MAX_HALF_PX", "SENSOR_MODIS"]:
        assert "'%s'" % k in linea, k
