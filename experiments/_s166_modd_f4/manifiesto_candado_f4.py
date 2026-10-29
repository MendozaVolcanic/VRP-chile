# -*- coding: utf-8 -*-
"""Manifiesto del candado de MOD-D fase 4 (PREREGISTRO_MODD_F4.md §8.8 y §11): el sha256 (con fin de línea LF) de cada
archivo del que dependen el arnés, el evaluador, la población, la identidad y sus pruebas.

POR QUÉ. El §8.8 pide un candado sobre todo lo que el A/B usa. Los jobs corren en el commit del tag (lo comprueba el
workflow), pero la LECTURA corre después, en otra máquina y con otro checkout: si entre el tag y la lectura alguien
cambia el evaluador, la población, el tablero o un módulo que importan, sin esto no lo vería nadie. El fin de línea se
normaliza a LF porque el checkout de Windows puede traer CRLF y el del runner LF (memoria S163, autocrlf): un mismo
archivo daría dos sha256.

CÓMO SE ARMA LA LISTA (no a mano): `--escribir` importa el arnés, el evaluador y la identidad en un proceso aparte y toma
todo módulo cargado desde el repositorio (experiments/, scripts/ y pipeline/), más los archivos fijos que leen (la
población, el tablero, los yaml que lee el código, el workflow, las pruebas). `comprobar` recalcula los sha256 y
devuelve {"estado": "OK"|"INDECIDIBLE", ...}: lo llaman el workflow (antes de correr) y externos_f4.py (antes de leer).

Lo que NO cubre: las grillas del censo en D:/vrp-trabajo/temporales/s162_modd/censo (fuera del repositorio; las lee
identidad_f4.py, que registra su propia procedencia) ni los artefactos del runner (los cubre la procedencia de
externos_f4.py: cabeceras con el commit del tag y el sha256 del tablero).

Las dos preguntas del instrumento: (1) si un archivo cambiara, ¿se vería? Sí: su sha256 cambia (probar_manifiesto
altera una copia). (2) Si el manifiesto estuviera vacío, incompleto o le faltara un obligatorio (la población o la
identidad, que hoy pueden no existir todavía), ¿se vería? Sí: da INDECIDIBLE, y el blob de evaluar_d25.py distinto de
1dbabf65 también.
Uso: python manifiesto_candado_f4.py --escribir | --comprobar
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
MANIFIESTO = AQUI / "MANIFIESTO_CANDADO_F4.json"
C = "experiments/_s166_modd_f4/"
FIJOS = [C + x for x in (
    "PREREGISTRO_MODD_F4.md", "poblacion_f4.json", "poblacion_f4.py", "contrato_poblacion_f4.py", "head_e.py",
    "identidad_f4.py", "probar_identidad_f4.py", "reetiquetado_f4.py", "probar_evaluar_f4.py", "evaluar_vacio.py",
    "mutar_evaluar_f4.py", "probar_mutar_f4.py", "probar_probe_f4.py", "humo_f4.txt", "manifiesto_candado_f4.py",
    "externos_f4.py", "ensayo_en_seco_f4.py")] + [
    "experiments/_s162_mxd03/k_en_sha.py", "experiments/_s157_prereg_d25/evaluar_d25.py", "frontend/index.html",
    ".github/workflows/probe-s168-modd-f4.yml", "volcanoes.yaml", "pipeline/grillas_mirova.yaml",
    "pipeline/profiles/mirova_equivalent.yaml"]
OBLIGATORIOS = (C + "probe_f4.py", C + "evaluar_f4.py", C + "poblacion_f4.json", C + "identidad_f4.py",
                C + "PREREGISTRO_MODD_F4.md", "frontend/index.html", "experiments/_s157_prereg_d25/evaluar_d25.py",
                ".github/workflows/probe-s168-modd-f4.yml", "pipeline/mirova_v750_codigo.py",
                "pipeline/process_modis.py", "pipeline/store.py", "scripts/banco_paridad.py")
D25 = ("experiments/_s157_prereg_d25/evaluar_d25.py", "1dbabf657407b6db0f91d9e2fc98eb16a8051873")
MIN_ARCHIVOS = 40
SONDA = r"""
import sys, os, json
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, sys.argv[1])
import probe_f4, evaluar_f4
if os.path.exists(os.path.join(sys.argv[1], "identidad_f4.py")):
    import identidad_f4
raiz = os.path.abspath(sys.argv[2])
print(json.dumps(sorted({os.path.abspath(m.__file__) for m in list(sys.modules.values())
                         if getattr(m, "__file__", None) and os.path.abspath(m.__file__).startswith(raiz)})))
"""


def sha256_lf(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def blob(p):
    b = Path(p).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def lista():
    r = subprocess.run([sys.executable, "-I", "-c", SONDA, str(AQUI), str(RAIZ)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1500:])
    mods = json.loads(r.stdout.strip().splitlines()[-1])
    rel = {Path(m).resolve().relative_to(RAIZ.resolve()).as_posix() for m in mods}
    rel = {x for x in rel if x.split("/")[0] in ("experiments", "scripts", "pipeline") and "__pycache__" not in x}
    return sorted(rel | set(FIJOS))


def escribir():
    arch = lista()
    existen = [a for a in arch if (RAIZ / a).exists()]
    faltan = sorted(set(arch) - set(existen))
    # tag y commit_tag quedan en None hasta que se cree el tag del candado: se llenan al regenerar justo antes del tag
    # (el sha del commit no puede ir dentro de un archivo de ese mismo commit; lo comprueba externos_f4.procedencia)
    m = {"tag": None, "commit_tag": None, "generado_utc": __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
         "archivos": {a: sha256_lf(RAIZ / a) for a in existen}, "faltaban_al_escribir": faltan}
    MANIFIESTO.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("manifiesto:", len(existen), "archivos; faltaban al escribir:", faltan or "ninguno")


def comprobar(ruta=MANIFIESTO, raiz=RAIZ):
    try:
        m = json.loads(Path(ruta).read_text(encoding="utf-8"))
        arch = m["archivos"]
    except Exception as e:  # noqa: BLE001
        return {"estado": "INDECIDIBLE", "motivo": f"manifiesto ilegible: {e}"}
    faltan = [a for a in arch if not (Path(raiz) / a).exists()]
    distintos = {a: sha256_lf(Path(raiz) / a) for a, h in arch.items()
                 if a not in faltan and sha256_lf(Path(raiz) / a) != h}
    obligatorios_fuera = [o for o in OBLIGATORIOS if o not in arch]
    d25 = (Path(raiz) / D25[0])
    blob_d25 = blob(d25) if d25.exists() else None
    incompleto = len(arch) < MIN_ARCHIVOS or bool(obligatorios_fuera) or bool(m.get("faltaban_al_escribir"))
    ok = not faltan and not distintos and not incompleto and blob_d25 == D25[1]
    return {"estado": "OK" if ok else "INDECIDIBLE", "n": len(arch), "faltan": faltan, "distintos": distintos,
            "obligatorios_fuera": obligatorios_fuera, "faltaban_al_escribir": m.get("faltaban_al_escribir"),
            "incompleto": incompleto, "blob_evaluar_d25": blob_d25}


def probar_manifiesto():
    """Una copia del manifiesto con un sha256 alterado tiene que dar INDECIDIBLE; una vacía y una sin la población,
    también. Y el manifiesto vigente sin tocar, si está completo, OK (si no lo está, se informa)."""
    import tempfile
    m = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "m.json"
        alt = json.loads(json.dumps(m))
        alt["archivos"][C + "evaluar_f4.py"] = "0" * 64
        p.write_text(json.dumps(alt), encoding="utf-8")
        assert comprobar(p)["estado"] == "INDECIDIBLE", "un sha256 alterado no se vio"
        p.write_text(json.dumps({"archivos": {}, "faltaban_al_escribir": []}), encoding="utf-8")
        assert comprobar(p)["estado"] == "INDECIDIBLE", "un manifiesto vacío pasó"
        sin = json.loads(json.dumps(m))
        sin["archivos"].pop(C + "poblacion_f4.json", None)
        p.write_text(json.dumps(sin), encoding="utf-8")
        assert comprobar(p)["estado"] == "INDECIDIBLE", "un manifiesto sin la población pasó"
    return True


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--escribir" in sys.argv:
        escribir()
    r = comprobar()
    print("comprobar:", {k: v for k, v in r.items() if k != "distintos"}, "| distintos:", list(r.get("distintos", {})))
    print("prueba del manifiesto:", probar_manifiesto())
    sys.exit(0 if r["estado"] == "OK" else 1)
