# -*- coding: utf-8 -*-
"""S157 - ¿Se puede separar el lado del barrido de la hora de la pasada?

POR QUE. La variante "+hora" de robustez_lado.py borra el efecto de lado. Antes de leer eso
como "el efecto era la hora", hay que ver si la hora y el lado son SEPARABLES: en una orbita
heliosincronica la hora solar local a la que el satelite pasa sobre un punto queda fijada por
cuan al este o al oeste del punto va la traza, o sea por el cenit con signo (+ este, - oeste).
Si la correlacion hora / cenit con signo es casi perfecta dentro de cada volcan, controlar por
hora es controlar por lado: las celdas volcan x tramo x hora que tienen pasadas de los dos lados
son sobre todo las de cenit bajo, donde el efecto es chico por geometria.

Mide, en el pareo PASADA de C0: (a) Spearman entre hora UTC y cenit con signo, por volcan y
sensor; (b) cenit mediano de los pares que sobreviven a las celdas "+hora" contra el total.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import medir_lado_del_barrido as m                                  # noqa: E402

OUT = os.path.join(HERE, "resultado_hora_y_lado.json")


def spearman(x, y):
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def main():
    frontera = m.aa.leer_frontera_k()
    pas, noche = m.cargar_alertas()
    regs = m.leer_registros(frontera)
    # (a) sobre TODOS los records nocturnos con lado (no solo los pareados)
    res = {"spearman_hora_vs_cenit_con_signo": {}, "celdas_hora": {}}
    por = defaultdict(list)
    for g in regs:
        if g["lado"] and "C0" in g["grupos"]:
            h = g["t"].hour + g["t"].minute / 60
            por[(g["vol"], g["bk"])].append((h, abs(g["sz"]) * (1 if g["lado"] == "E" else -1)))
    for (v, bk), l in sorted(por.items()):
        if len(l) >= 30:
            h, z = zip(*l)
            res["spearman_hora_vs_cenit_con_signo"][f"{v}|{bk}"] = {"n": len(l), "rho": round(spearman(h, z), 3)}
    # (b) que pares sobreviven a las celdas volcan x tramo x hora
    base = [f for f in m.parear(regs, pas, noche)["PASADA"] if "C0" in f["grupos"]]
    for bk in ("v375", "v750"):
        fs = [f for f in base if f["bk"] == bk]
        cel = defaultdict(lambda: [0, 0])
        for f in fs:
            cel[(f["vol"], f["bin"], f["dt"][11:13])][0 if f["lado"] == "E" else 1] += 1
        vivos = [f for f in fs if min(cel[(f["vol"], f["bin"], f["dt"][11:13])]) >= m.MIN_CELDA]
        res["celdas_hora"][bk] = {
            "n_total": len(fs), "n_en_celdas_hora": len(vivos),
            "cenit_mediano_total": round(float(np.median([abs(f["sz"]) for f in fs])), 2),
            "cenit_mediano_en_celdas_hora": round(float(np.median([abs(f["sz"]) for f in vivos])), 2) if vivos else None,
            "frac_cenit_ge35_total": round(sum(abs(f["sz"]) >= 35 for f in fs) / len(fs), 3),
            "frac_cenit_ge35_en_celdas_hora": round(sum(abs(f["sz"]) >= 35 for f in vivos) / len(vivos), 3) if vivos else None,
        }
    print(json.dumps(res, indent=1, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
