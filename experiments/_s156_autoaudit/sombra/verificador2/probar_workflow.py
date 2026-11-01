"""C4: extrae los `run:` del workflow con yaml y los ejecuta con un `gh` falso (registra los argumentos),
sobre un sombra_latest.json sintético. No toca GitHub. Uso: python probar_workflow.py <raiz> <dir_trabajo>"""
import json
import os
import shutil
import subprocess
import sys

import yaml

raiz, trabajo = sys.argv[1:3]
wf = yaml.safe_load(open(os.path.join(raiz, ".github/workflows/vigilancia-sombra.yml"), encoding="utf-8"))
print("claves raiz:", list(wf.keys()))
print("on:", wf["on"])
steps = {s.get("name"): s for s in wf["jobs"]["vigilar"]["steps"]}
script = steps["Open issue"]["run"]
open(os.path.join(trabajo, "open_issue.sh"), "w", encoding="utf-8", newline="\n").write(script)
commit = steps["Commit results"]["run"]
open(os.path.join(trabajo, "commit.sh"), "w", encoding="utf-8", newline="\n").write(commit)
print("bash -n open_issue:", subprocess.run(["bash", "-n", os.path.join(trabajo, "open_issue.sh")],
                                            capture_output=True, text=True).returncode)

BIN = os.path.join(trabajo, "bin")
os.makedirs(BIN, exist_ok=True)
GH = r'''#!/bin/bash
echo "GH $*" >> "$GHLOG"
if [ "$1 $2" = "issue list" ]; then
  if [ "$GH_FALLA" = "1" ]; then echo "error de red" >&2; exit 1; fi
  echo "${GH_ABIERTOS:-0}"; exit 0
fi
if [ "$1 $2" = "issue create" ]; then
  shift 2
  while [ $# -gt 0 ]; do case "$1" in --title) echo "TITLE<<$2>>" >> "$GHLOG"; shift 2;; --body) printf 'BODY<<%s>>\n' "$2" >> "$GHLOG"; shift 2;; *) shift;; esac; done
  exit 0
fi
'''
open(os.path.join(BIN, "gh"), "w", newline="\n").write(GH)

BASE = {"veredicto": "VERDE", "reversion": [], "muy_bajo": {}, "persistencia": [],
        "negativos_VIIRS375": {"k": 0, "n": 9, "wilson": [0, 0.3], "cota_ab": 0.05, "dispara": False}, "avisos": []}
REV = dict(BASE, veredicto="REVERSION_CANDIDATA",
           reversion=[{"volcano": "PuyehueCordonCaulle", "sensor": "VIIRS750", "fecha_utc": "2026-10-20 05:54",
                       "vrp_mirova_mw": 1.19}],
           avisos=["aviso con 100% y una barra \\ invertida y comillas \"x\" y $HOME"])
INV = dict(BASE, veredicto="INVESTIGAR", persistencia=[{"volcano": "Isluga", "noches": ["2026-10-20", "2026-10-21", "2026-10-22"]}])
CIEGA = {"veredicto": "VIGILANCIA_CIEGA", "avisos": ["no se leyeron DATOS_K_DESDE_UTC"]}

ESC = [("falla_script", BASE, {"OUTCOME": "failure"}),
       ("reversion", REV, {"OUTCOME": "success"}),
       ("reversion_ya_abierto", REV, {"OUTCOME": "success", "GH_ABIERTOS": "1"}),
       ("investigar", INV, {"OUTCOME": "success"}),
       ("ciega_temprana", CIEGA, {"OUTCOME": "success"}),
       ("verde", BASE, {"OUTCOME": "success"}),
       ("gh_list_falla", REV, {"OUTCOME": "success", "GH_FALLA": "1"})]
for nombre, d, env in ESC:
    w = os.path.join(trabajo, "esc_" + nombre)
    shutil.rmtree(w, ignore_errors=True)
    os.makedirs(os.path.join(w, "data/audit_continuous"))
    json.dump(d, open(os.path.join(w, "data/audit_continuous/sombra_latest.json"), "w", encoding="utf-8"))
    log = os.path.join(w, "gh.log")
    e = dict(os.environ, GHLOG=log, GITHUB_SERVER_URL="https://github.com", GITHUB_REPOSITORY="o/r",
             GITHUB_RUN_ID="123", PATH=BIN + os.pathsep + os.environ["PATH"], **env)
    # GitHub corre bash con -e -o pipefail
    p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", os.path.join(trabajo, "open_issue.sh")],
                       cwd=w, env=e, capture_output=True, text=True, encoding="utf-8")
    print(f"=== {nombre}: rc={p.returncode}")
    print("   stdout:", p.stdout.strip().replace("\n", " | ")[:300])
    if p.stderr.strip():
        print("   stderr:", p.stderr.strip()[:300])
    if os.path.exists(log):
        print("   gh.log:", open(log, encoding="utf-8").read().strip().replace("\n", " ¶ ")[:900])
