# -*- coding: utf-8 -*-
"""S160 (hallazgo 247 de docs/AUDIT_S160.md): todo paso de un workflow con cron que corre el pipeline con
credenciales de Earthdata se detiene en seco si EARTHDATA_TOKEN viene vacio.

POR QUE: un secret ausente en GitHub Actions llega como texto vacio, no como error. Sin token, earthaccess cae
al par usuario y clave, que esta vencido: medido en S160 (experiments/_s160_audit/f3/ y v3/), cada job hace 8
logins en unos 1.300 s, hasta 88 por corrida con la matriz de 11 volcanes, y la cuenta de Earthdata se bloquea
(regla A71). experimental-diario.yml ya tenia la guarda; nrt.yml, el productor de produccion, no.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GUARDA = '-z "$EARTHDATA_TOKEN"'


def _pasos_cron_con_pipeline():
    for f in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        y = yaml.safe_load(f.read_text(encoding="utf-8"))
        on = y.get("on") or y.get(True) or {}
        if not (isinstance(on, dict) and "schedule" in on):
            continue
        for job, j in (y.get("jobs") or {}).items():
            for paso in j.get("steps") or []:
                env, run = paso.get("env") or {}, paso.get("run") or ""
                if "EARTHDATA_TOKEN" in env and "run_pipeline.py" in run:
                    yield f.name, job, paso.get("name", ""), run


def test_hay_pasos_que_medir():
    """Control: si el filtro dejara de encontrar pasos, el test de abajo pasaria sin mirar nada."""
    nombres = {(w, n) for w, _, n, _ in _pasos_cron_con_pipeline()}
    assert any(w == "nrt.yml" for w, _ in nombres), nombres


def test_todo_paso_cron_con_pipeline_corta_si_el_token_viene_vacio():
    sin = [(w, j, n) for w, j, n, run in _pasos_cron_con_pipeline()
           if GUARDA not in run or run.index(GUARDA) > run.index("run_pipeline.py")]
    assert not sin, f"pasos con cron que llaman al pipeline sin cortar antes por token vacio: {sin}"
