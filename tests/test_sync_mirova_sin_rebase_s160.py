# -*- coding: utf-8 -*-
"""Guard S160 (R13 de la auditoría de Mirova-v1, hallazgo H-V1): el sync del CSV de MIROVA no rebasa.

POR QUÉ. `latest_consolidado.csv` se reemplaza entero en cada sync y el scraper lo escribe ordenado sólo por
`timestamp`, así que cada versión llega con las filas en otro orden. Cuando el push perdía la carrera, el bucle
hacía `git pull --rebase -X theirs` y git mezclaba como TEXTO tres permutaciones del mismo archivo: en hunks que
considera limpios deja filas dos veces o ninguna. El commit 81dd25ce3 (2026-08-19 17:41, 822 duplicados y 163
llaves menos) se reproduce byte a byte con un rebase así de sus tres entradas reales
(`D:\\vrp-trabajo\\mirova-v1-auditoria\\07_reproduccion_vrp_sync.py`, salida `salida_07.txt`).

Arreglo: si el push se rechaza, volver a `origin/main`, bajar de nuevo los dos CSV y regenerar los JSON con el
mismo script, y antes de cada push una guarda que exige llaves únicas (Volcan, Sensor, Fecha_Satelite_UTC).

Contrato que vigila:
1. La guarda da rojo sobre 81dd25ce3 y verde sobre su padre 10fa8a934 (datos reales de la historia).
2. La guarda da rojo si el instrumento queda ciego (archivo vacío o sin las columnas de la llave).
3. El workflow no tiene `rebase` ni `-X theirs/ours`; dentro del bucle: reset a origin/main, se vuelve a correr
   el script de sincronización, la guarda corre antes del push, y al agotar intentos sale en rojo.
"""
import io
import os
import re
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GUARDA = os.path.join(ROOT, "scripts", "guarda_llaves_consolidado.py")
WF = os.path.join(ROOT, ".github", "workflows", "sync-mirova-csv.yml")
CABECERA = ("timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,Distancia_km,Tipo_Registro,"
            "Clasificacion Mirova,Ruta Foto,Fecha_Proceso_GitHub,Ultima_Actualizacion,Editado,"
            "Fecha_Proceso_UTC,Ultima_Actualizacion_UTC\n")
FILA_A = "1792635600,2026-10-22 02:20:00,x,Tupungatito,MODIS,0.0,0.0,RUTINA,NULO,No,a,b,NO,c,d\n"
FILA_B = "1792635600,2026-10-22 02:20:00,x,Lascar,MODIS,0.0,0.0,RUTINA,NULO,No,a,b,NO,c,d\n"


def _guarda(tmp_path, contenido, nombre="c.csv"):
    p = tmp_path / nombre
    p.write_bytes(contenido if isinstance(contenido, bytes) else contenido.encode("utf-8"))
    return subprocess.run([sys.executable, GUARDA, str(p)], capture_output=True, text=True)


def test_guarda_verde_sin_llaves_repetidas(tmp_path):
    r = _guarda(tmp_path, CABECERA + FILA_A + FILA_B)
    assert r.returncode == 0, r.stdout + r.stderr


def test_guarda_roja_con_una_llave_repetida(tmp_path):
    # Misma llave, distinto VRP: la guarda mira la llave, no la línea entera.
    r = _guarda(tmp_path, CABECERA + FILA_A + FILA_B + FILA_A.replace(",0.0,0.0,", ",1.5,0.0,"))
    assert r.returncode == 1, r.stdout + r.stderr


@pytest.mark.parametrize("contenido", ["", CABECERA, "a,b,c\n1,2,3\n"])
def test_guarda_roja_si_el_instrumento_queda_ciego(tmp_path, contenido):
    r = _guarda(tmp_path, contenido)
    assert r.returncode == 1, f"vacío, sin filas o sin columnas de la llave debe dar rojo: {r.stdout}{r.stderr}"


def _blob(ref):
    r = subprocess.run(["git", "show", f"{ref}:latest_consolidado.csv"], cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        pytest.skip(f"{ref} no está en este clon (checkout superficial); la prueba sobre datos reales corre en local")
    return r.stdout


@pytest.mark.parametrize("ref,esperado", [("81dd25ce3", 1), ("10fa8a934", 0)])
def test_guarda_sobre_la_copia_corrupta_real_y_su_padre(tmp_path, ref, esperado):
    r = _guarda(tmp_path, _blob(ref), nombre=f"{ref}.csv")
    assert r.returncode == esperado, f"{ref}: rc={r.returncode}\n{r.stdout}{r.stderr}"
    if esperado == 1:
        assert "822" in r.stdout, f"81dd25ce3 tiene 822 llaves repetidas medidas: {r.stdout}"


@pytest.fixture(scope="module")
def paso_push():
    with io.open(WF, encoding="utf-8") as fh:
        wf = yaml.safe_load(fh)
    pasos = wf["jobs"]["sync"]["steps"]
    return next(p["run"] for p in pasos if "git push" in (p.get("run") or ""))


def test_workflow_no_rebasa():
    with io.open(WF, encoding="utf-8") as fh:
        texto = fh.read()
    codigo = "\n".join(l.split("#", 1)[0] for l in texto.splitlines())
    assert "rebase" not in codigo, "el sync no debe rebasar: mezcla el CSV como texto (H-V1)"
    assert not re.search(r"-X\s*(theirs|ours)", codigo)


def test_bucle_regenera_sobre_origin_main_y_guarda_antes_del_push(paso_push):
    bucle = re.search(r"for attempt in[^\n]*\n(.*?)\n\s*done", paso_push, re.S)
    assert bucle, "falta el bucle de reintento"
    cuerpo = bucle.group(1)
    i_reset = cuerpo.find("git reset --hard origin/main")
    i_sync = cuerpo.find("scripts/sync_mirova_csv.sh")
    i_guarda = cuerpo.find("scripts/guarda_llaves_consolidado.py")
    i_push = cuerpo.find("git push")
    assert -1 not in (i_reset, i_sync, i_guarda, i_push), (i_reset, i_sync, i_guarda, i_push)
    assert i_reset < i_sync < i_push, "tras el reset hay que volver a bajar y regenerar antes de empujar"
    assert i_guarda < i_push, "la guarda de llaves corre antes del push"
    resto = paso_push[bucle.end():]
    assert re.search(r"exit 1", resto), "al agotar los intentos el paso sale en rojo"
