# -*- coding: utf-8 -*-
"""Corre SOLO el G3 (noches intactas) de evaluar_diurno.py sobre una o más raíces, sin la referencia, sin G1 ni G2.

Por qué existe (desviación D2 del pre-registro, 2026-10-17): para comprobar que el veredicto del G3 no depende del
orden en que `unir_intentos.py` unió los intentos, hay que correrlo sobre la misma ventana unida en los dos órdenes.
Correr el evaluador entero mostraría además G1 y G2, que no se miran mientras W5 y W6 no terminen. Este script pasa
por las MISMAS funciones del evaluador (`cargar_brazo`, `noches_identicas`, `veredicto_g3`), así que no es otra
implementación del G3.

Uso: python g3_solo.py --raiz <dir> [--raiz <dir> ...] [--out g3.json]
     (cada raíz trae _s151_ab_diurno_control/<volcan>.json y _s151_ab_diurno_on/<volcan>.json)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import evaluar_diurno as ED  # noqa: E402  (deja sys.stdout en utf-8)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", action="append", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    coords = ED.bp._coords_por_volcan()
    inner = ED.bp.inner_desde_html()
    rc, _ = ED.cargar_brazo(a.raiz, "control", coords, inner)
    rd, _ = ED.cargar_brazo(a.raiz, "diurno", coords, inner)
    ni = ED.noches_identicas(rc, rd)
    g3 = ED.veredicto_g3(ni)
    print("raíces %s" % a.raiz)
    print("records nocturnos control %d, diurno %d | faltan %d, sobran %d | versión o gránulo distintos %d"
          % (ni["n_control"], ni["n_diurno"], ni["faltan"], ni["sobran"], ni["version_distinta"]))
    print("pares nocturnos por categoría: %s" % ni["estados"])
    for est in ("orden", "borde", "hotspot_escena"):
        for x in ni["admitidos"][est]:
            print("   %-14s %s" % (est, x))
    for x in ni["ejemplos"]:
        print("   distinto       %s" % x)
    print("G3 -> %s" % g3)
    if a.out:
        Path(a.out).write_text(json.dumps(dict(ni, G3=g3), ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
