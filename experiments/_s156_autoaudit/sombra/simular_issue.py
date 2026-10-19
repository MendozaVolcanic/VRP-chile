"""Simula el paso 'Open issue' de vigilancia-sombra.yml con un gh falso, en cuatro escenarios.
Uso: python simular_issue.py <raiz_worktree> <json_real> <carpeta_trabajo>"""
import json
import os
import subprocess
import sys

import yaml

raiz, real, T = sys.argv[1:4]
wf = yaml.safe_load(open(os.path.join(raiz, ".github/workflows/vigilancia-sombra.yml"), encoding="utf-8"))
run = next(s["run"] for s in wf["jobs"]["vigilar"]["steps"] if s.get("name") == "Open issue")
stub = ('gh() {\n'
        '  if [ "$1 $2" = "issue list" ]; then echo "$FAKE_NUM"; return; fi\n'
        '  echo "GH-CALL:"; for a in "$@"; do echo "[$a]"; done\n'
        '}\n')
os.makedirs(os.path.join(T, "data/audit_continuous"), exist_ok=True)
open(os.path.join(T, "paso.sh"), "w", encoding="utf-8", newline="\n").write(stub + run)
base = json.load(open(real, encoding="utf-8"))
rev = dict(base, veredicto="REVERSION_CANDIDATA",
           reversion=[{"volcano": "X", "sensor": "MODIS", "fecha_utc": "2026-10-25 07:20", "vrp_mirova_mw": 2.0}])
ciega = dict(base, veredicto="VIGILANCIA_CIEGA", avisos=["la sombra de Llaima no produce hace 5 días"])
fuera = dict(rev, veredicto="CANDIDATA_FUERA_DE_PLAZO")
casos = [("fuera de plazo, sin issue abierto", fuera, "success", ""),
         ("reversion, sin issue abierto", rev, "success", ""),
         ("reversion, con issue abierto 901", rev, "success", "901"),
         ("ciega, sin issue abierto", ciega, "success", ""),
         ("verde", base, "success", ""),
         ("script caido", base, "failure", "")]
for nombre, obj, outcome, num in casos:
    json.dump(obj, open(os.path.join(T, "data/audit_continuous/sombra_latest.json"), "w", encoding="utf-8"))
    env = dict(os.environ, OUTCOME=outcome, FAKE_NUM=num, GITHUB_SERVER_URL="https://github.com",
               GITHUB_REPOSITORY="x/y", GITHUB_RUN_ID="1")
    r = subprocess.run(["bash", "-eo", "pipefail", "paso.sh"], cwd=T, env=env, capture_output=True, text=True, encoding="utf-8")
    print(f"=== {nombre} (rc {r.returncode})")
    print(r.stdout.strip()[:900])
    if r.stderr.strip():
        print("STDERR:", r.stderr.strip()[:400])
