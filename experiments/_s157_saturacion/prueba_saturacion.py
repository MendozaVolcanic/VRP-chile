# -*- coding: utf-8 -*-
"""C-SIN del probe de saturación: el contador sobre arreglos sintéticos, sin red. ESCRITO ANTES DE CORRER EL PROBE.

POR QUÉ (A110, A116). Un cero del probe sólo vale si el contador PUEDE dar distinto de cero. Acá se arma una escena
de 9 x 9 con bits y topes puestos a mano y se exige que el contador los encuentre todos y sólo esos, que la cota de
energía de un píxel perdido sea k·A·(L - L_anillo), y que una escena sin nada dé ceros en todo.
Uso: python experiments/_s157_saturacion/prueba_saturacion.py   (sale 1 si algo falla)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import probe_saturacion as ps  # noqa: E402


def escena(con_saturacion):
    sh = (9, 9)
    lut_max = 367.0
    bt_mir = np.full(sh, 270.0)
    bt_tir = np.full(sh, 265.0)
    qf_mir = np.zeros(sh, dtype=np.int64)
    qf_tir = np.zeros(sh, dtype=np.int64)
    if con_saturacion:
        bt_mir[4, 4] = lut_max          # MIR saturada: tope de la LUT y bit 4
        qf_mir[4, 4] = 4
        qf_tir[4, 5] = 4                # sólo la TIR saturada: MIR sana a 330 K
        bt_mir[4, 5] = 330.0
        qf_mir[3, 3] = 2                # Out_of_Range, no se pierde
        qf_mir[0, 0] = 4                # fuera de la ventana
    raw = {"I04": {"dn": np.zeros(sh, dtype=np.int64), "qf": qf_mir, "bt": bt_mir, "lut_max": lut_max,
                   "qf_attrs": {}, "valid_max": None},
           "I05": {"dn": np.zeros(sh, dtype=np.int64), "qf": qf_tir, "bt": bt_tir, "lut_max": 380.0,
                   "qf_attrs": {}, "valid_max": None}}
    pipe = {"I04": np.where((qf_mir & 4) != 0, np.nan, bt_mir), "I05": np.where((qf_tir & 4) != 0, np.nan, bt_tir)}
    yy, xx = np.mgrid[0:9, 0:9]
    dist = np.hypot(yy - 4, xx - 4) * 0.375
    return raw, pipe, dist


def main():
    fallas = []
    k_area, t_bg, lam = 2531250.0, 270.0, 3.74
    for con in (True, False):
        raw, pipe, dist = escena(con)
        c0 = [(4, 3)]
        ven, _, cum, vec = ps.mascaras(dist.shape, dist, 1.0, c0)
        cont, perdido = ps.contar_viirs(raw, pipe, "I04", "I05", ven, cum, vec)
        filas = ps.cota_viirs(raw, "I04", perdido, ven, t_bg, lam, k_area, dist)
        got = (cont["I04"]["ventana"]["bit4_sat"], cont["I05"]["ventana"]["bit4_sat"], cont["I04"]["ventana"]["bit2_oor"],
               cont["I04"]["ventana"]["tope_lut"], int((perdido & ven).sum()), cont["I04"]["vecinos_cumulo"]["bit4_sat"])
        esperado = (1, 1, 1, 1, 2, 1) if con else (0, 0, 0, 0, 0, 0)
        print("con_saturacion=%s conteos %s esperado %s" % (con, got, esperado))
        if got != esperado:
            fallas.append("conteos %s" % con)
        L = lambda t: float(ps.planck(np.array([t]), lam)[0])  # noqa: E731
        cota_esp = ((L(367.0) - L(t_bg)) + (L(330.0) - L(t_bg))) * k_area / 1e6 if con else 0.0
        cota = sum(f["mw"] for f in filas)
        print("   cota %.4f MW esperada %.4f" % (cota, cota_esp))
        if abs(cota - cota_esp) > 1e-9:
            fallas.append("cota %s" % con)
    print("FALLAS: %s" % fallas if fallas else "C-SIN OK")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
