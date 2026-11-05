# -*- coding: utf-8 -*-
"""Arma el manifiesto del candado de la prueba retrospectiva (pre-registro SELLADO PREREGISTRO_RETRO_PAQUETE.md, tag
s173-prereg-retro-sellado, §11 y control «Candado» del §6).

POR QUÉ. El candado dice «lo que se lee es lo que se selló». Si el manifiesto se calculara sobre el disco, un archivo
editado sin commitear entraría como sellado; por eso cada sha256 sale de `git show <ref>:<ruta>`, con el fin de línea
normalizado a LF (`\\r` quitado, lección S171 y S-B del segundo verificador del pre-registro). El ref es el tag del
despacho (s172-retro-dN): el manifiesto se arma una vez, antes de leer F26, y no se toca.

También comprueba que el pre-registro no cambió desde el sello (§11: «git diff <commit del sello> --
PREREGISTRO_RETRO_PAQUETE.md vacío al leer, y su sha256 LF igual al del tag del sello»). El pre-registro vive en la rama
loop/activo, no en main: por eso se compara el blob del tag del sello contra el de `--ref-preregistro`.

Uso: python armar_manifiesto.py --ref s172-retro-d2 --referencia RUTA [--referencia RUTA ...] [--osf RUTA]
     [--ref-preregistro origin/loop/activo] --salida manifiesto.json
Salida: 0 armado; 3 el pre-registro cambió desde el sello (no se escribe el manifiesto).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
TAG_SELLO = "s173-prereg-retro-sellado"
PREREGISTRO = "experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md"

_spec = importlib.util.spec_from_file_location("leer_retro_para_manifiesto", AQUI / "leer_retro.py")
L = importlib.util.module_from_spec(_spec)
sys.modules["leer_retro_para_manifiesto"] = L
_spec.loader.exec_module(L)


def _blob(ref, ruta):
    r = subprocess.run(["git", "show", f"{ref}:{ruta}"], cwd=RAIZ, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"MANIFIESTO: {ruta} no existe en {ref}")
    return r.stdout


def sha256_lf_blob(b):
    return hashlib.sha256(b.replace(b"\r", b"")).hexdigest()


def rutas_requeridas(referencias=()):
    """Lo que el candado del lector exige siempre (REQUERIDOS_MANIFIESTO, que incluye MANIFIESTO_REGLAS) más las
    referencias congeladas y el OSF de la corrida."""
    return sorted(set(L.REQUERIDOS_MANIFIESTO) | set(L.MANIFIESTO_REGLAS) | set(referencias))


def manifiesto(ref, rutas):
    return {r: sha256_lf_blob(_blob(ref, r)) for r in rutas}


def verificar_preregistro(ref_prereg, tag_sello=TAG_SELLO):
    sello = sha256_lf_blob(_blob(tag_sello, PREREGISTRO))
    actual = sha256_lf_blob(_blob(ref_prereg, PREREGISTRO))
    return {"tag_sello": tag_sello, "ref": ref_prereg, "sello": sello, "actual": actual, "igual": sello == actual}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="tag del despacho (s172-retro-dN)")
    ap.add_argument("--referencia", action="append", default=[], help="ruta en el repo de una referencia congelada")
    ap.add_argument("--osf", help="ruta en el repo del OSF v2.5 (0863c240…)")
    ap.add_argument("--ref-preregistro", default="origin/loop/activo")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)
    pr = verificar_preregistro(a.ref_preregistro)
    print("PRE-REGISTRO:", pr)
    if not pr["igual"]:
        print("CANDADO: el pre-registro cambió desde el sello; no se arma el manifiesto")
        return 3
    refs = list(a.referencia) + ([a.osf] if a.osf else [])
    m = manifiesto(a.ref, rutas_requeridas(refs))
    Path(a.salida).write_text(json.dumps(m, indent=1, sort_keys=True), encoding="utf-8")
    print(f"MANIFIESTO: {len(m)} archivos desde {a.ref} -> {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
