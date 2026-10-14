# -*- coding: utf-8 -*-
"""Estudio D, parte 1: cuantas alertas de la referencia unificada tienen VRP de 0,05 MW o menos.

POR QUE. El scraper de Mirova-v1 marca ALERTA toda pasada con VRP mayor que 0 dentro de su radio; el banner de
MIROVA dice NONE en algunas de 0,02 a 0,05 MW (docs/S151_CRITERIO_CLASE_MIROVA.md §5). Antes de decidir como
contarlas hay que saber cuantas son, de que sensor, de que volcan y en que tramo de calidad de la referencia
(A119). Se cuenta por pasada, no por fila (377 pasadas estan en el consolidado y en el OCR a la vez).

Uso: python censo.py   (escribe nada; la salida se guarda con `> censo_salida.txt`)
"""
import io
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from comun import UMBRAL_MINIMA_MW, TRAMOS, pasadas_de_alerta, tramo  # noqa: E402


def main():
    P = pasadas_de_alerta()
    print(f"pasadas con fila de alerta en la referencia unificada: {len(P)}")
    print(f"  nocturnas (las que miran los evaluadores): {sum(v['nocturna'] for v in P.values())}")
    print()
    print("VRP minimo de alerta por sensor (todas las pasadas) y conteo de los valores mas bajos:")
    for s in ("VIIRS375", "VIIRS750", "MODIS"):
        vs = sorted(v["vrp"] for k, v in P.items() if k[1] == s)
        c = Counter(round(x, 2) for x in vs if x <= 0.1)
        print(f"  {s:8s} n={len(vs):5d} min={vs[0]:.2f}  valores <= 0,10: {dict(sorted(c.items()))}")
    # VIIRS 750: en mayo MIROVA dio NONE con 0,15 MW y VERY LOW con 0,18 (frontera_salida.txt, muestra C).
    v750 = [v for k, v in P.items() if k[1] == "VIIRS750"]
    print(f"  VIIRS750 alertas con VRP <= 0,15: {sum(v['vrp'] <= 0.15 + 1e-9 for v in v750)} "
          f"(nocturnas {sum(v['vrp'] <= 0.15 + 1e-9 and v['nocturna'] for v in v750)}); "
          f"de 0,16 a 0,17: {sum(0.155 < v['vrp'] < 0.175 for v in v750)}")
    print()
    for etiqueta, sel in (("TODAS", lambda v: True), ("NOCTURNAS", lambda v: v["nocturna"])):
        Q = {k: v for k, v in P.items() if sel(v)}
        m = {k: v for k, v in Q.items() if v["vrp"] <= UMBRAL_MINIMA_MW + 1e-9}
        print(f"== {etiqueta}: alertas con VRP <= {UMBRAL_MINIMA_MW} MW: {len(m)} de {len(Q)} ({100 * len(m) / len(Q):.1f} %)")
        print(f"   de ellas: VRP 0,05 exacto {sum(abs(v['vrp'] - 0.05) < 1e-9 for v in m.values())}, "
              f"<= 0,04 {sum(v['vrp'] <= 0.04 + 1e-9 for v in m.values())}; solo OCR {sum(v['solo_ocr'] for v in m.values())}")
        print("   por sensor (minimas / alertas del sensor):")
        for s in ("VIIRS375", "VIIRS750", "MODIS"):
            n = sum(1 for k in Q if k[1] == s); x = sum(1 for k in m if k[1] == s)
            print(f"     {s:8s} {x:4d} / {n:4d}" + (f"  ({100 * x / n:.1f} %)" if n else ""))
        print("   por volcan (minimas / alertas, todos los sensores):")
        for vol in sorted({k[0] for k in Q}):
            n = sum(1 for k in Q if k[0] == vol); x = sum(1 for k in m if k[0] == vol)
            print(f"     {vol:20s} {x:4d} / {n:4d}  ({100 * x / n:.1f} %)")
        print("   por tramo A119 (minimas / alertas; minimas solo OCR):")
        for nombre, _, _ in TRAMOS:
            n = sum(1 for k in Q if tramo(k[2]) == nombre); x = [k for k in m if tramo(k[2]) == nombre]
            so = sum(m[k]["solo_ocr"] for k in x)
            print(f"     {nombre:62s} {len(x):4d} / {n:4d}" + (f"  ({100 * len(x) / n:.1f} %)" if n else "") + f"  solo OCR {so}")
        print("   por mes de satelite (minimas / alertas):")
        mes = defaultdict(lambda: [0, 0])
        for k in Q:
            mes[k[2][:7]][0] += 1
            mes[k[2][:7]][1] += k in m
        for mm, (n, x) in sorted(mes.items()):
            print(f"     {mm}  {x:4d} / {n:4d}  ({100 * x / n:.1f} %)")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
