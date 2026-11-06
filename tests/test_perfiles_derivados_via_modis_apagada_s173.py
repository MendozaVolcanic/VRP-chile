# -*- coding: utf-8 -*-
"""S173 (ronda 3 del PR A; V1-04 y patrón 6 de experiments/_s173_aud/v1/INFORME.md): los tres perfiles derivados que no
deben seguir a la réplica en MODIS declaran la vía «código MIROVA» apagada en su propio YAML, ya en el PR A.

POR QUÉ: el PR B enciende `enable_modis_codigo_mirova` en mirova_equivalent y estos tres perfiles heredan de él. El
laboratorio (`experimental`, congelado en C0 y sombra de K de la vigilancia), `experimental_ndc_focus` (producción de
antes de K) y `_s146_ab_control` (ancla de tests/produccion_pre_k.py) heredarían la vía en silencio (A117). En A la
declaración es inerte (el padre está apagado); viene aquí para que un `git revert` de B no la arrastre consigo y el
significado de los tres no dependa de que B esté o no. Se lee como la lee el pipeline: en `thresholds:` (A89).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFILES = ("experimental", "experimental_ndc_focus", "_s146_ab_control")


@pytest.mark.parametrize("perfil", PERFILES)
def test_el_yaml_declara_la_via_de_modis_apagada_en_thresholds(perfil):
    d = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{perfil}.yaml").read_text(encoding="utf-8"))
    assert (d.get("thresholds") or {}).get("enable_modis_codigo_mirova") is False, perfil


@pytest.mark.parametrize("perfil", PERFILES)
def test_el_pipeline_la_lee_apagada(perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "False"
