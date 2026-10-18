# -*- coding: utf-8 -*-
"""S154 (tarea 1.32): los brazos del A/B diurno sobre K son la réplica K y la réplica K con la rama diurna.

POR QUÉ. El A/B diurno W2 a W6 corrió sobre C0 y su NO ADOPTAR no se traslada a K: de día el Test 1 integrado dispara
en 2.000 de las 2.077 publicaciones de VIIRS 375 en negativos limpios (verificador limpio,
`experiments/_s151_ab_diurno/salidas/W2_W6_s154/verificador/INFORME.md`, H4). Para repetirlo sobre K, el control tiene
que ser EXACTAMENTE producción y el brazo diurno tiene que diferir sólo en la palanca; si no, el A/B mide otra cosa
sin dar error (A117). Se comprueba resolviendo todas las constantes de `pipeline.profile` (nunca el YAML, A89).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTROL, DIURNO = "_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on"

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
        assert cfg["output"]["data_subdir"] == n   # el workflow exige DATA_SUBDIR == PROFILE_NAME


def test_control_es_produccion_y_diurno_difiere_solo_en_la_palanca():
    res = _resolver("mirova_equivalent", CONTROL, DIURNO)
    prod, c, d = res["mirova_equivalent"], res[CONTROL], res[DIURNO]
    assert len(prod) > 100   # el instrumento ve las constantes de verdad
    assert _distintos(prod, c) == {"PROFILE_NAME", "DATA_SUBDIR"}, sorted(_distintos(prod, c))
    assert _distintos(c, d) == {"PROFILE_NAME", "DATA_SUBDIR", "ENABLE_DAYTIME_VIIRS"}, sorted(_distintos(c, d))
    assert (c["ENABLE_DAYTIME_VIIRS"], d["ENABLE_DAYTIME_VIIRS"]) == ("False", "True")
    # la base es K (S153, #850): sin Test 1 integrado, conectiva max, banda 22 MODIS
    for x in (c, d):
        assert (x["ENABLE_TEST1_PATH"], x["ENABLE_TESTS_23_PROSE_BRANCH"], x["ENABLE_MODIS_B22_PRIMARY"]) == \
            ("False", "True", "True")
        assert x["ENABLE_DAYTIME_MODIS"] == "False"


def test_el_workflow_no_fija_el_nombre_del_brazo_diurno():
    src = (ROOT / ".github" / "workflows" / "reproc-s151-ab-diurno.yml").read_text(encoding="utf-8")
    assert "p.PROFILE_NAME == '_s151_ab_diurno_on'" not in src
    assert "ARM_CONTROL" in src.split("El brazo LEE lo que declara")[1].split("Reproceso del brazo")[0]
