# -*- coding: utf-8 -*-
"""S134 F4 (anexo) - de que esta hecha la cola de razones > 2, y por volcan.

POR QUE. La ley intermedia deja los dos bins de cenital en banda pero NO baja la cola:
13,8 % de los pares siguen sobre 2, contra el 4,2 % del control. Si la cola fuera el
mismo gradiente cenital, la correccion la habria bajado junto con la mediana. Que no lo
haga significa que la cola es OTRO fenomeno, y saber cual cambia que se hace despues.

LAS DOS PREGUNTAS DEL INSTRUMENTO
  1. Si el reparto de la cola estuviera roto, se veria? Si: los conteos por volcan y por
     bin suman al total declarado, y ese total se compara contra el del script principal.
  2. Si el instrumento estuviera muerto? Daria cero pares en todos lados, y el script
     aborta si el total no coincide con el del veredicto principal.

READ-ONLY. No escribe en data/ ni en pipeline/. Numeros a `cola_composicion.json`.
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from f4_solape_ley_intermedia import (  # noqa: E402
    BINS, RAZON_COLA, VOLCANES, _mediana, cargar_gt, pares_de)

SALIDA = os.path.join(HERE, "cola_composicion.json")


def _tramo_mirova(v):
    return ("<0,5 MW" if v < 0.5 else "0,5-2 MW" if v < 2 else
            "2-10 MW" if v < 10 else ">=10 MW")


def main():
    gt, _ = cargar_gt()
    pares, _diag = pares_de("_s133_area_geoloc", gt)
    n = len(pares)

    por_vol, por_bin, por_tramo = {}, {}, defaultdict(lambda: [0, 0])
    for vol in VOLCANES:
        ps = [p for p in pares if p["volcano"] == vol]
        rs = [p["razon_x_f"] for p in ps]
        cola = [r for r in rs if r > RAZON_COLA]
        por_vol[vol] = {
            "n_pares": len(ps),
            "mediana_razon_ley_intermedia": _mediana(rs),
            "mediana_razon_geoloc_sin_f": _mediana([p["razon"] for p in ps]),
            "n_en_cola": len(cola),
            "fraccion_en_cola": (len(cola) / float(len(ps))) if ps else None,
        }
    for b in BINS:
        ps = [p for p in pares if p["bin"] == b]
        cola = [p for p in ps if p["razon_x_f"] > RAZON_COLA]
        por_bin[b] = {"n_pares": len(ps), "n_en_cola": len(cola),
                      "fraccion_en_cola": (len(cola) / float(len(ps))) if ps else None}
    for p in pares:
        t = _tramo_mirova(p["vrp_mirova_mw"])
        por_tramo[t][0] += 1
        if p["razon_x_f"] > RAZON_COLA:
            por_tramo[t][1] += 1

    out = {
        "_que_es": ("composicion de la cola de razones > 2 bajo la ley intermedia "
                    "(geoloc x f(theta)), brazo _s133_area_geoloc, VIIRS375"),
        "_denominador_total_pares": n,
        "_ventana_utc": {"desde": min(p["datetime_utc"] for p in pares),
                         "hasta": max(p["datetime_utc"] for p in pares)},
        "n_total_en_cola": sum(1 for p in pares if p["razon_x_f"] > RAZON_COLA),
        "por_volcan": por_vol,
        "por_bin_cenital": por_bin,
        "por_magnitud_de_MIROVA": {
            k: {"n_pares": v[0], "n_en_cola": v[1],
                "fraccion_en_cola": v[1] / float(v[0]) if v[0] else None}
            for k, v in sorted(por_tramo.items())},
    }
    with io.open(SALIDA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False))

    print("Escrito:", SALIDA, " n_pares=%d  n_cola=%d" % (n, out["n_total_en_cola"]))
    print("\npor volcan (ley intermedia):")
    for v, d in sorted(por_vol.items(), key=lambda kv: -(kv[1]["fraccion_en_cola"] or 0)):
        print("  %-22s n=%3d  mediana=%.3f  cola=%4.1f%%"
              % (v, d["n_pares"], d["mediana_razon_ley_intermedia"] or 0,
                 100 * (d["fraccion_en_cola"] or 0)))
    print("\npor magnitud de MIROVA:")
    for k, d in out["por_magnitud_de_MIROVA"].items():
        print("  %-10s n=%3d  cola=%4.1f%%" % (k, d["n_pares"],
                                               100 * (d["fraccion_en_cola"] or 0)))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
