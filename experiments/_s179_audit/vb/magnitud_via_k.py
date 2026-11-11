#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador VB, auditoría S179. Afirmación 456 por otro camino: el salto de magnitud que verá el operador el día
del encendido, medido pasada a pasada (VRP que MUESTRA el tablero con la vía dividido por el que muestra con K, en la
misma pasada, cuando los dos publican), sin pasar por MIROVA. El auditor midió la razón de medianas contra MIROVA, sólo
en pasadas con alerta de MIROVA; aquí entran todas las pasadas que los dos publican.

«Muestra» y «publica»: banco_paridad.cargar_nuestros de main 438a60a1e (el predicado del tablero con node), campos
`disp` y `pub`. Vía = data/sombra_codigo_mirova; K = data/guardia_k_viirs (K pura, mismo gránulo).

Las dos preguntas del instrumento.
1. Si lo medido estuviera roto, ¿lo vería? Control nulo: K de la guardia contra K de producción en las mismas pasadas
   tiene que dar razón 1,000 exacta (n mayor que 0). Si el montaje leyera un solo lado, la vía también daría 1.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Cada cifra lleva su n; n = 0 se imprime SIN DATO.
Uso: python magnitud_via_k.py <carpeta de datos con sombra_codigo_mirova, guardia_k_viirs y mirova_equivalent> <desde> <hasta>
"""
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path(r"D:\vrp-trabajo\temporales\s179-audit\main")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
for p in (str(MAIN), str(MAIN / "scripts")):
    sys.path.insert(0, p)
import vigilancia_guardia_viirs as vv  # noqa: E402
import banco_paridad as bp  # noqa: E402

aa, vg = vv.aa, vv.vg
DATOS = Path(sys.argv[1])
WIN = (sys.argv[2], sys.argv[3])


def cargar(carpeta, sensor, coords, inner):
    return [r for r in bp.cargar_nuestros(coords, inner, WIN, data=DATOS / carpeta) if r["b"] == sensor]


def razones(a, b):
    ib = defaultdict(list)
    for r in b:
        ib[r["vol"]].append(r)
    out = defaultdict(list)
    for r in a:
        par = [x for x in ib[r["vol"]] if abs((x["dt"] - r["dt"]).total_seconds()) <= vg.TOL_S]
        if not par or not r["pub"] or not par[0]["pub"] or not par[0]["disp"]:
            continue
        q = r["disp"] / par[0]["disp"]
        out[r["vol"]].append(q)
        out["TODOS"].append(q)
    return out


def main():
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    print(f"datos {DATOS}; ventana {WIN}")
    for sensor in ("VIIRS375", "VIIRS750"):
        via = cargar("sombra_codigo_mirova", sensor, coords, inner)
        gk = cargar("guardia_k_viirs", sensor, coords, inner)
        pk = cargar("mirova_equivalent", sensor, coords, inner)
        ctl = razones(gk, pk)["TODOS"]
        print(f"\n== {sensor}: vía {len(via)} records, guardia K {len(gk)}")
        if ctl:
            print(f"   control nulo K guardia / K producción: n {len(ctl)}, mediana {statistics.median(ctl):.4f}, "
                  f"mín {min(ctl):.4f}, máx {max(ctl):.4f}")
        else:
            print("   control nulo: SIN DATO")
        r = razones(via, gk)
        if not r:
            print("   SIN DATO")
        for vol in sorted(r, key=lambda v: (v == "TODOS", v)):
            q = sorted(r[vol])
            print(f"   {vol:20s} n {len(q):3d}  mediana vía/K {statistics.median(q):.2f}  "
                  f"cuartiles {q[len(q) // 4]:.2f} a {q[(3 * len(q)) // 4]:.2f}  mín {q[0]:.2f}  máx {q[-1]:.2f}")
    print("\nsalida 0")


if __name__ == "__main__":
    main()
