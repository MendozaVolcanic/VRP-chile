# -*- coding: utf-8 -*-
"""S195: el record de una misma pasada sintética, con el código de ANTES (tag pre-s195-laboratorio-paso3) y el de
DESPUÉS (este árbol), byte a byte, en los perfiles que no encienden la zona A y en el brazo s = 5,0.

POR QUÉ. Las pruebas de CI comparan perfiles dentro de un mismo árbol (tests/test_laboratorio_paso3_s195.py P1 y P2):
prueban que la zona apagada o con s = 5 es producción, pero no que producción sea la misma que antes del cambio. El CI
no tiene el tag (checkout de profundidad 1), así que esto se corre en local y su salida queda en salida_identidad.txt.

CÓMO. git archive del tag (pipeline/, scripts/, volcanoes.yaml) a una carpeta temporal, con la pasada sintética de
este árbol copiada adentro (la del tag no tiene la escena débil; el script sólo arma el gránulo y llama a los
procesadores, que son los del árbol donde vive). Cada perfil y escena corre en un subproceso por árbol (el perfil se
lee al importar). Cada familia por separado, para que un error de una (los perfiles de la guardia K no leen el
gránulo falso por los lectores de la vía) no oculte a las otras: un error tiene que ser el mismo antes y después.

Uso: python experiments/_s195_lab_paso3/identidad_antes_despues.py <carpeta_temporal>
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
TAG = "pre-s195-laboratorio-paso3"
PERFILES = ("mirova_equivalent", "laboratorio", "guardia_k_modis", "guardia_k_viirs", "sombra_34")
ENVOLTORIO = r'''
import json, sys, traceback
sys.path.insert(0, "tests")
import _pasada_sintetica_laboratorio as S
out = {}
for f in ("MODIS", "VIIRS750", "VIIRS375"):
    try:
        out[f] = S.correr(f, sys.argv[1])
    except Exception as e:
        out[f] = {"ERROR": type(e).__name__ + ": " + str(e)[:200]}
print("@@" + json.dumps(out, default=float, sort_keys=True))
'''


def correr(arbol: Path, perfil: str, escena: str) -> dict:
    r = subprocess.run([sys.executable, "-c", ENVOLTORIO, escena], cwd=arbol, capture_output=True, text=True,
                       env=dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8"), timeout=900)
    lineas = [l for l in r.stdout.splitlines() if l.startswith("@@")]
    if r.returncode != 0 or not lineas:
        return {"PROCESO": f"rc={r.returncode} {r.stderr[-300:]}"}
    return json.loads(lineas[-1][2:])


def main() -> int:
    tmp = Path(sys.argv[1])
    antes = tmp / "arbol_antes"
    if antes.exists():
        shutil.rmtree(antes)
    antes.mkdir(parents=True)
    tar = tmp / "antes.tar"
    subprocess.run(["git", "archive", "-o", str(tar), TAG, "pipeline", "scripts", "volcanoes.yaml"], cwd=RAIZ,
                   check=True)
    with tarfile.open(tar) as t:
        t.extractall(antes, filter="data")
    (antes / "tests").mkdir()
    shutil.copy(RAIZ / "tests" / "_pasada_sintetica_laboratorio.py", antes / "tests")
    sha = subprocess.run(["git", "rev-parse", TAG + "^{commit}"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    print(f"antes: {TAG} ({sha}); después: {RAIZ}")
    n_igual = n_dist = n_err_igual = 0
    for escena in ("calor", "debil"):
        for perfil in PERFILES:
            a, d = correr(antes, perfil, escena), correr(RAIZ, perfil, escena)
            for fam in ("MODIS", "VIIRS750", "VIIRS375"):
                ra, rd = a.get(fam, a), d.get(fam, d)
                igual = json.dumps(ra, sort_keys=True) == json.dumps(rd, sort_keys=True)
                es_error = "ERROR" in ra or "PROCESO" in ra
                n_igual += igual and not es_error
                n_err_igual += igual and es_error
                n_dist += not igual
                vrp = (rd.get("record", rd) if isinstance(rd, dict) else {}).get("vrp_mw")
                print(f"{escena:6s} {perfil:18s} {fam:9s} {'IGUAL' if igual else 'DISTINTO'}"
                      f"{' (error igual antes y después)' if igual and es_error else ''} vrp_mw={vrp}")
        # el brazo s = 5,0 (sólo existe después) contra producción de antes
        a, d = correr(antes, "mirova_equivalent", escena), correr(RAIZ, "_s195_lab_s50", escena)
        for fam in ("MODIS", "VIIRS750", "VIIRS375"):
            igual = json.dumps(a[fam], sort_keys=True) == json.dumps(d[fam], sort_keys=True)
            n_igual += igual
            n_dist += not igual
            print(f"{escena:6s} {'s50 vs prod antes':18s} {fam:9s} {'IGUAL' if igual else 'DISTINTO'} "
                  f"vrp_mw={d[fam].get('vrp_mw')}")
    print(f"TOTAL: {n_igual} iguales con record, {n_err_igual} iguales con error, {n_dist} distintos")
    return 0 if n_dist == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
