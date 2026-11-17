# -*- coding: utf-8 -*-
"""S190, adenda V (experiments/_s190_diurno/ADENDA_VIA.md, sellada): los brazos del A/B diurno sobre la vía.

POR QUÉ. El A/B sólo mide la palanca si el control ES producción (la vía en los tres sensores) y el brazo diurno
difiere de él sólo en los dos flags del día. Se comprueba resolviendo TODAS las constantes de pipeline.profile, no
leyendo el YAML (A89), y con el aislamiento de directorio que exige A47.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTROL, DIURNO = "_s190_ab_diurno_via_control", "_s190_ab_diurno_via_on"

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


def test_los_perfiles_escriben_en_su_propio_directorio():
    for n in (CONTROL, DIURNO):
        cfg = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{n}.yaml").read_text(encoding="utf-8"))
        assert cfg["extends"] == "mirova_equivalent"
        assert cfg["output"]["data_subdir"] == n


def test_control_es_produccion_y_diurno_difiere_solo_en_los_dos_flags_del_dia():
    res = _resolver("mirova_equivalent", CONTROL, DIURNO)
    prod, c, d = res["mirova_equivalent"], res[CONTROL], res[DIURNO]
    assert len(prod) > 100
    assert _distintos(prod, c) == {"PROFILE_NAME", "DATA_SUBDIR"}, sorted(_distintos(prod, c))
    assert _distintos(c, d) == {"PROFILE_NAME", "DATA_SUBDIR", "ENABLE_DAYTIME_VIIRS", "ENABLE_DAYTIME_MODIS"}, \
        sorted(_distintos(c, d))
    for k in ("ENABLE_DAYTIME_VIIRS", "ENABLE_DAYTIME_MODIS"):
        assert (c[k], d[k]) == ("False", "True")
    for x in (c, d):
        for k in ("ENABLE_MODIS_CODIGO_MIROVA", "ENABLE_V375_CODIGO_MIROVA", "ENABLE_V750_CODIGO_MIROVA"):
            assert x[k] == "True", k
