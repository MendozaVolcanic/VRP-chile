# -*- coding: utf-8 -*-
"""F4T (S175), instrumento 2: ejecuta el bloque `run:` del paso «Run VRP pipeline — mirova_equivalent profile» de
nrt.yml tal como está escrito, con bash, con EARTHDATA_TOKEN vacío, y mira si llega a invocar python
(= a scripts/run_pipeline.py = a fetch.auth()). Lo mismo para guardia-k-modis.yml y sombra-34.yml.

Línea base roja (1) del plan: el nrt.yml de ANTES de #894 (`git show 79b4e3af6^:.github/workflows/nrt.yml`) con token
vacío tiene que llegar a python (hallazgo 247 de S160). Si este instrumento no lo reencuentra, está ciego.

Las dos preguntas:
1. Si la guarda estuviera rota (o ausente), ¿se ve? Sí: el shim de python escribe una marca en un archivo cuando lo
   invocan; con la guarda sana la marca no aparece y el exit es 1 con «::error::EARTHDATA_TOKEN vacío».
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: control positivo = el mismo bloque con token «x»
   tiene que invocar al shim (marca presente, exit 0).

Sin red: python real nunca corre (el shim lo reemplaza en el PATH); no hay credenciales.
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE_WF = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v4t\rerun_f4t\base_wf")
TMP = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v4t\rerun_f4t\tmp_02")
TMP.mkdir(parents=True, exist_ok=True)
BASH = r"C:\Program Files\Git\bin\bash.exe"

CASOS = [
    # (etiqueta, archivo yml, nombre del paso que contiene)
    ("nrt.yml BASE 752d348bc", BASE_WF / "nrt.yml", "mirova_equivalent profile"),
    ("nrt.yml PRE-#894 (79b4e3af6^)  <- línea base roja (1)", BASE_WF / "nrt_pre894.yml", "mirova_equivalent profile"),
    ("guardia-k-modis.yml BASE", BASE_WF / "guardia-k-modis.yml", "perfil guardia_k_modis"),
    ("sombra-34.yml BASE", BASE_WF / "sombra-34.yml", "perfil sombra_34"),
    ("experimental-diario.yml BASE", BASE_WF / "experimental-diario.yml", "experimental"),
]


def bloque_run(yml: Path, fragmento: str) -> str:
    y = yaml.safe_load(yml.read_text(encoding="utf-8"))
    for job in y["jobs"].values():
        for paso in job.get("steps", []):
            if fragmento in (paso.get("name") or "") and paso.get("run"):
                return paso["run"]
    raise SystemExit(f"paso con «{fragmento}» no encontrado en {yml.name}")


def shim_dir() -> Path:
    d = TMP / "shim"
    d.mkdir(exist_ok=True)
    marca = (TMP / "python_invocado.txt").as_posix()
    for nombre in ("python", "python3"):
        (d / nombre).write_text(
            "#!/bin/bash\n"
            f"echo \"SHIM python: $*\" >> '{marca}'\n"
            "echo \"SHIM python ejecutado (sin red, sin pipeline): $*\"\n"
            "exit 0\n", encoding="utf-8", newline="\n")
        os.chmod(d / nombre, 0o755)
    return d


def correr(etiqueta: str, run: str, token: str) -> None:
    marca = TMP / "python_invocado.txt"
    if marca.exists():
        marca.unlink()
    script = run.replace("${{ matrix.volcano }}", "Lascar").replace("${{ github.sha }}", "0" * 40)
    # Cualquier otra expresión ${{ }} que quede se vacía (inputs del dispatch): en el cron son nulos.
    script = re.sub(r"\$\{\{[^}]*\}\}", "", script)
    sh = TMP / "paso.sh"
    sh.write_text(script, encoding="utf-8", newline="\n")
    env = {
        "PATH": shim_dir().as_posix() + ":/usr/bin:/bin",
        "EARTHDATA_TOKEN": token,
        "EARTHDATA_USERNAME": "usuario-falso", "EARTHDATA_PASSWORD": "clave-falsa",
        "VRP_DATE": "", "VRP_START": "", "VRP_END": "", "VRP_OVERWRITE": "", "VRP_MEDIR": "",
        "GITHUB_OUTPUT": (TMP / "gh_output.txt").as_posix(),
        "DISPATCH_VOLCANO": "",
    }
    (TMP / "gh_output.txt").write_text("", encoding="utf-8")
    r = subprocess.run([BASH, sh.as_posix()], capture_output=True, text=True, env=env, cwd=TMP, timeout=60)
    invocado = marca.exists()
    salida = (r.stdout + r.stderr).strip().splitlines()
    primera = next((ln for ln in salida if "::error::" in ln or "SHIM" in ln or "perfil" in ln), salida[0] if salida else "")
    print(f"- {etiqueta} | token={'VACÍO' if token == '' else repr(token)} | exit={r.returncode} | "
          f"python invocado={'SÍ' if invocado else 'NO'} | {primera[:110]}")
    if invocado:
        for ln in marca.read_text(encoding="utf-8").splitlines():
            print(f"      {ln[:150]}")


print("Bloque `run:` de cada paso, ejecutado con bash y un shim de python en el PATH (nunca corre el pipeline).\n")
for etiqueta, yml, frag in CASOS:
    run = bloque_run(yml, frag)
    tiene_guarda = '-z "$EARTHDATA_TOKEN"' in run
    print(f"[{etiqueta}] guarda `-z \"$EARTHDATA_TOKEN\"` en el texto: {'SÍ' if tiene_guarda else 'NO'}")
    correr(etiqueta, run, "")
    correr(etiqueta + " (control positivo)", run, "x")
    print()
