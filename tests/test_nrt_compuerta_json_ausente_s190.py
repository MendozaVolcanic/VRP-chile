# -*- coding: utf-8 -*-
"""S190 (auditoría de Codex, ronda 2, F6-108, CONFIRMADO gravedad 2 por el verificador Claude del frente 6,
D:\\codex-vrp\\_salida\\ronda2\\f6_verificacion\\VEREDICTO.md): la compuerta inmediata del NRT («Assert Tier A records
fresh (A57)» en .github/workflows/nrt.yml) salía en verde si el JSON de un volcán principal no existía.

POR QUÉ: el caso se escribió como «primera corrida», pero los 11 volcanes principales tienen historia desde 2025-02-15;
un JSON ausente es un archivo borrado o un commit roto, la misma clase de falla nuestra e inmediata que «0 records», que
la compuerta ya deja en rojo. En verde, la falta sólo la veía el healthcheck al día siguiente.

Se corre el bloque Python real del paso, extraído del workflow, en una carpeta temporal.
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
WF = RAIZ / ".github" / "workflows" / "nrt.yml"


def _script(volcan):
    wf = yaml.safe_load(WF.read_text(encoding="utf-8"))
    pasos = [p for job in wf["jobs"].values() for p in job.get("steps", [])
             if p.get("name") == "Assert Tier A records fresh (A57)"]
    assert len(pasos) == 1, "el paso de la compuerta cambió de nombre"
    run = pasos[0]["run"]
    cuerpo = run[run.index("<<'PYEOF'\n") + len("<<'PYEOF'\n"):run.rindex("PYEOF")]
    return cuerpo.replace("${{ matrix.volcano }}", volcan)


def _correr(tmp_path, volcan, contenido=None):
    d = tmp_path / "data" / "mirova_equivalent"
    d.mkdir(parents=True)
    if contenido is not None:
        (d / f"{volcan}.json").write_text(contenido, encoding="utf-8")
    return subprocess.run([sys.executable, "-c", _script(volcan)], cwd=tmp_path, capture_output=True, text=True)


def test_json_ausente_de_un_tier_a_deja_rojo(tmp_path):
    r = _correr(tmp_path, "Lascar")
    assert r.returncode == 1, r.stdout + r.stderr
    assert re.search(r"FAIL .*no existe", r.stdout), r.stdout


def test_control_cero_records_sigue_rojo(tmp_path):
    assert _correr(tmp_path, "Lascar", '{"records": []}').returncode == 1


def test_control_dato_fresco_sigue_verde(tmp_path):
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = _correr(tmp_path, "Lascar", '{"records": [{"datetime_utc": "%s"}]}' % ahora)
    assert r.returncode == 0, r.stdout + r.stderr
