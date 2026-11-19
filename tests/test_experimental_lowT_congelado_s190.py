# -*- coding: utf-8 -*-
"""S190 (F8-112 y F8-V301 de la auditoría de Codex, ronda 2, CONFIRMADOS por verificador de contexto limpio en
D:\\codex-vrp\\_salida\\ronda2\\f8b_verificacion\\VEREDICTO.md): experimental_lowT declara las tres vías «código MIROVA»
apagadas, como experimental.yaml.

POR QUÉ: experimental_lowT es el piloto VRPTIR (Aveni 2025) y su cabecera dice congelar el detector de antes de K. Pero
hereda de mirova_equivalent, que desde S172 y S186 enciende las tres vías, y no las declaraba: el cargador lo resolvía
con las tres en True. Como los 45 volcanes tienen grilla de MIROVA en los tres sensores, cada procesador retornaba el
record de la vía (process_viirs.py, `return _rec` del bloque de la vía) antes del camino K, que es el único donde se
calcula el diagnóstico VRPTIR (`_compute_vrptir_aveni_diagnostic`). El piloto corría sin producir su campo y con otro
detector del que decía. Se lee como la lee el pipeline: en `thresholds:` (A89).
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFIL = "experimental_lowT"
VIAS = ("enable_v750_codigo_mirova", "enable_v375_codigo_mirova", "enable_modis_codigo_mirova")


@pytest.mark.parametrize("clave", VIAS)
def test_el_yaml_declara_la_via_apagada_en_thresholds(clave):
    d = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{PERFIL}.yaml").read_text(encoding="utf-8"))
    assert (d.get("thresholds") or {}).get(clave) is False, clave


def test_el_pipeline_resuelve_las_vias_apagadas_y_vrptir_encendido():
    env = dict(os.environ, VRP_PROFILE=PERFIL, PYTHONDONTWRITEBYTECODE="1")
    code = ("import pipeline.profile as p; print(p.ENABLE_V750_CODIGO_MIROVA, p.ENABLE_V375_CODIGO_MIROVA, "
            "p.ENABLE_MODIS_CODIGO_MIROVA, p.ENABLE_VRPTIR_AVENI)")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "False False False True"
