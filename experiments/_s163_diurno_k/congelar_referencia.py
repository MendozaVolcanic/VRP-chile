# -*- coding: utf-8 -*-
"""Extrae los 4 CSV de la referencia de MIROVA tal como estaban en un commit, para evaluar contra la misma base que
el pre-registro (PREREGISTRO.md §8). La copia del árbol se actualiza cada hora (sync-mirova-csv.yml): evaluar contra
ella mediría otra referencia que la del sustrato.

Uso: python -I experiments/_s163_diurno_k/congelar_referencia.py --commit 047bd5692 --salida <carpeta nueva>
Comprueba al final los sha256 contra sustrato_k.json y sale con error si no coinciden.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(AQUI))

import sustrato_k as sk  # noqa: E402


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sustrato", default=str(AQUI / "sustrato_k.json"))
    ap.add_argument("--sin-comprobar", action="store_true", help="sólo para generar el sustrato por primera vez")
    a = ap.parse_args(argv)
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=False)
    for nombre, ruta in sk.ORIGEN_REF.items():
        datos = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (a.commit, ruta)], capture_output=True,
                               check=True).stdout
        (out / nombre).write_bytes(datos)
    if a.sin_comprobar:
        for n in sk.ARCHIVOS_REF:
            print("%s %s" % (sk.sha256(out / n), n))
        return 0
    esperado = json.loads(Path(a.sustrato).read_text(encoding="utf-8"))["sha256"]
    malos = [n for n in sk.ARCHIVOS_REF if sk.sha256(out / n) != esperado[n]]
    for n in sk.ARCHIVOS_REF:
        print("%s %s %s" % (sk.sha256(out / n), n, "OK" if n not in malos else "DISTINTO"))
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
