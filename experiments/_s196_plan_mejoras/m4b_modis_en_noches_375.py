# -*- coding: utf-8 -*-
"""Medición previa de MEJ-4 (plan S196): ¿MODIS publica menos en los volcanes donde su caja deja el cráter afuera?

POR QUÉ. La vía no ancla la grilla al cráter: la centra en el punto de referencia de MIROVA. En MODIS usa la caja `def`
(5 × 5 celdas al centro) en los 11, y en Tupungatito y Cordón Caulle el cráter queda fuera de esa región sensible, a
2,11 y 5,25 km (`docs/MIROVA_DIVERGENCES.md` D36 punto 7). Si eso calla al cráter, MODIS debería publicar mucho menos
en esos dos volcanes en las noches en que VIIRS 375 ya publica la cumbre (VIIRS 375 usa la caja C13 en el cráter, así
que sirve de testigo físico de que esa noche había calor). Es una cuenta descriptiva: MODIS ve píxeles de 1 km y
cuatro veces menos sensibles que el de 375 m, así que su tasa es baja en todos; lo que importa es el contraste entre
volcanes con el cráter dentro y fuera de la caja.

Qué hace: noches (volcán, fecha UTC) con alguna pasada VIIRS 375 publicada (predicado del tablero) y con algún record
MODIS esa noche; de ésas, en cuántas MODIS publica. 2026-03-01 a 2026-11-22, data/mirova_equivalent.

Uso: python experiments/_s196_plan_mejoras/m4b_modis_en_noches_375.py
"""
import collections
import importlib.util
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent


def _cargar(nombre, archivo):
    s = importlib.util.spec_from_file_location(nombre, AQUI / archivo)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


M3 = _cargar("m3", "m3_cumbre_375_sin_750.py")
M7 = _cargar("m7", "m7_modis_sobre_rutina.py")
bp = M3.bp
FUERA = {"Tupungatito": "2,11 km", "PuyehueCordonCaulle": "5,25 km"}


def main():
    v = M3.cargar("2026-03-01", "2026-11-22")
    m = M7.cargar_modis("2026-03-01", "2026-11-22")
    n375 = collections.defaultdict(set)
    for r in v:
        if r["b"] == "VIIRS375" and r["pub"]:
            n375[r["vol"]].add(r["dt"].date())
    mod_rec = collections.defaultdict(set)
    mod_pub = collections.defaultdict(set)
    for r in m:
        mod_rec[r["vol"]].add(r["dt"].date())
        if r["pub"]:
            mod_pub[r["vol"]].add(r["dt"].date())
    print("noches con VIIRS 375 publicado y algún record MODIS; de ellas, con MODIS publicado (2026-03-01 a 2026-11-22)")
    print("%-20s %8s %8s %8s  %s" % ("volcán", "noches", "MODIS", "%", "cráter fuera de la caja MODIS"))
    for vol in bp.VOLS:
        base = n375[vol] & mod_rec[vol]
        if not base:
            continue
        k = len(base & mod_pub[vol])
        print("%-20s %8d %8d %7.0f%%  %s" % (vol, len(base), k, 100.0 * k / len(base), FUERA.get(vol, "")))


if __name__ == "__main__":
    main()
