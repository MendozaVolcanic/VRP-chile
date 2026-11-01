"""Verificador 5: extrae del workflow el bloque python del detalle del issue y lo corre sobre un sombra_latest
sintetico con una candidata fuera de plazo. Uso: python e3_snippet_workflow.py <raiz_worktree> <dir_tmp>"""
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml

raiz, tmp = Path(sys.argv[1]), Path(sys.argv[2])
wf = yaml.safe_load((raiz / ".github/workflows/vigilancia-sombra.yml").read_text(encoding="utf-8"))
run = next(s["run"] for j in wf["jobs"].values() for s in j["steps"] if s.get("name") == "Open issue")
cuerpo = run.split("<<'PY' > /tmp/detalle.txt\n", 1)[1].split("\nPY\n", 1)[0]
cuerpo = textwrap.dedent(cuerpo)
(tmp / "data/audit_continuous").mkdir(parents=True, exist_ok=True)
p = {"volcano": "Villarrica", "sensor": "MODIS", "fecha_utc": "2027-03-01 07:20", "vrp_mirova_mw": 2.0}
(tmp / "data/audit_continuous/sombra_latest.json").write_text(json.dumps(
    {"veredicto": "CANDIDATA_FUERA_DE_PLAZO", "reversion": [], "fuera_de_plazo": [p], "persistencia": [],
     "muy_bajo": {}, "negativos_VIIRS375": {}, "avisos": []}), encoding="utf-8")
r = subprocess.run([sys.executable, "-c", cuerpo], cwd=tmp, capture_output=True, text=True)
print("rc", r.returncode, "| stdout:", r.stdout.strip(), "| stderr:", r.stderr.strip()[-300:])
