#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría S179, frente B. ¿Qué perfiles cambian de detector al mergear #974 (B1) y #983 (B2 sobre B1)?

POR QUÉ. B1 y B2 encienden un flag en `pipeline/profiles/mirova_equivalent.yaml`. Todo perfil que hereda de producción
(`extends: mirova_equivalent`) y no declara el flag lo hereda encendido. Si un perfil que corre en un workflow (una
sombra, una guardia, un control K) hereda la vía sin que nadie lo decida, el PR enciende más de lo aprobado.

QUÉ HACE. Arma tres copias chicas de `pipeline/` (sólo ese paquete, 2,5 MB): main 438a60a1e, main + los perfiles de
#974 (bbbe2068d) y main + los perfiles de #983 (e68819484). En cada una resuelve, con `pipeline.profile` en un proceso
aparte (A89), los tres flags de la vía para CADA perfil, y lista los que cambian.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si estuviera roto lo que mido, ¿lo vería? Sí: `mirova_equivalent` tiene que cambiar de False a True (control
   positivo). Si no cambia, el montaje no lee los perfiles del PR.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Un perfil que no resuelve se informa como ERROR, nunca como
   «sin cambio»; se cuenta cuántos perfiles se resolvieron.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path(r"D:\vrp-trabajo\temporales\s179-audit\main")
REPO = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
TMP = Path(r"D:\vrp-trabajo\temporales\s179-audit\b\overlays")
AQUI = Path(__file__).resolve().parent
REFS = {"main_438a60a1e": None, "pr974_bbbe2068d": "bbbe2068d", "pr983_e68819484": "e68819484"}
FLAGS = ["ENABLE_V375_CODIGO_MIROVA", "ENABLE_V750_CODIGO_MIROVA", "ENABLE_MODIS_CODIGO_MIROVA"]


def git(*args):
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    return subprocess.run(["git", *args], cwd=REPO, env=env, capture_output=True, check=True).stdout


def armar(nombre, ref):
    destino = TMP / nombre
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(MAIN / "pipeline", destino / "pipeline")
    if ref:
        cambiados = git("diff", "--name-only", f"438a60a1e...{ref}", "--", "pipeline/").decode().split()
        for ruta in cambiados:
            (destino / ruta).write_bytes(git("show", f"{ref}:{ruta}"))
        return cambiados
    return []


def resolver(raiz, perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    codigo = ("import json, pipeline.profile as p; print('@@' + json.dumps({k: getattr(p, k) for k in "
              + repr(FLAGS) + "}))")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=raiz, env=env, capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    for linea in r.stdout.splitlines():
        if linea.startswith("@@"):
            return json.loads(linea[2:])
    return {"ERROR": (r.stderr or r.stdout)[-200:]}


def main():
    res = {}
    for nombre, ref in REFS.items():
        cambiados = armar(nombre, ref)
        print(f"== {nombre}: archivos de pipeline/ que el PR cambia: {cambiados}")
        perfiles = sorted(p.stem for p in (TMP / nombre / "pipeline" / "profiles").glob("*.yaml"))
        res[nombre] = {p: resolver(TMP / nombre, p) for p in perfiles}
        n_err = sum(1 for v in res[nombre].values() if "ERROR" in v)
        print(f"   perfiles: {len(perfiles)}; resueltos {len(perfiles) - n_err}; con error {n_err}")
    base = res["main_438a60a1e"]
    for nombre in ("pr974_bbbe2068d", "pr983_e68819484"):
        print(f"\n== perfiles cuyo flag efectivo cambia de main a {nombre}")
        n = 0
        for p, v in res[nombre].items():
            b = base.get(p)
            if b != v:
                n += 1
                cambios = {k: (b.get(k) if b else None, v.get(k)) for k in FLAGS if (b or {}).get(k) != v.get(k)}
                print(f"   {p}: {cambios or v}")
        print(f"   total {n} de {len(res[nombre])}")
    print("\n== en main, perfiles con alguna vía de VIIRS encendida:",
          sorted(p for p, v in base.items() if v.get(FLAGS[0]) or v.get(FLAGS[1])))
    print("== con #983, perfiles con las dos vías de VIIRS apagadas:",
          sorted(p for p, v in res["pr983_e68819484"].items() if v.get(FLAGS[0]) is False and v.get(FLAGS[1]) is False))
    errores = {n: {p: v for p, v in r.items() if "ERROR" in v} for n, r in res.items()}
    print("== errores:", json.dumps(errores, ensure_ascii=False)[:1500])
    with open(AQUI / "flags_por_perfil_salida.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    shutil.rmtree(TMP, ignore_errors=True)
    print("salida 0")


if __name__ == "__main__":
    main()
