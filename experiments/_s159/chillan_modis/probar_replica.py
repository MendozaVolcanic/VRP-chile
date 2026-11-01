# -*- coding: utf-8 -*-
"""Prueba sintetica de replica.py contra las funciones de produccion (corre en Windows, no necesita HDF).

Control positivo: un pixel caliente sembrado en el centro tiene que salir en la mascara de las dos (original y
replica), y apagar la compuerta o cambiar la conectiva tiene que cambiar el conteo en las dos por igual.
Sale con codigo 1 si alguna mascara difiere.
"""
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.detection_context import first_pass_tests_2_and_3, second_pass_adjacent  # noqa: E402
from replica import replicar_first_pass, replicar_second_pass  # noqa: E402


def escena(seed, caliente=0.04, frio_bt=False):
    rng = np.random.default_rng(seed)
    n = 80
    nti = -0.92 + rng.normal(0, 0.003, (n, n))
    nti_app = nti + rng.normal(0, 0.001, (n, n))
    bt = 272 + rng.normal(0, 1.5, (n, n))
    nti[40, 40] += caliente
    bt[40, 40] += 1.0 if frio_bt else 8.0
    nti[41, 40] += caliente / 3
    yy, xx = np.mgrid[0:n, 0:n]
    dist = np.hypot(yy - 40, xx - 40) * 1.0
    roi = dist < 30
    return nti, nti_app, bt, roi, dist


def main():
    fallas = 0
    kw = dict(c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5, c2_deti_summit=5, inner_km=5,
              c1_dnti_scene=0.010, c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10)
    for seed in range(4):
        for frio in (False, True):
            nti, nti_app, bt, roi, dist = escena(seed, frio_bt=frio)
            for prose in (True, False):
                for gate in (True, False):
                    h, d = first_pass_tests_2_and_3(nti, nti_app, bt, roi, dist, 272.0, 3.0, use_prose_branch=prose,
                                                    apply_bt_gate=gate, **kw)
                    r = replicar_first_pass(nti, nti_app, bt, roi, dist, 272.0, 3.0, use_prose_branch=prose,
                                            apply_bt_gate=gate, **kw)
                    igual = bool(np.array_equal(h, r["hot"]))
                    fallas += not igual
                    print(f"seed={seed} frio={frio} prose={prose} gate={gate} n_orig={int(h.sum())} "
                          f"n_rep={int(r['hot'].sum())} centro_orig={bool(h[40, 40])} igual={igual}")
                    sp = second_pass_adjacent(nti, d["eti"], h, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5, c2_deti=5,
                                              is_summit=dist <= 5, c1_dnti_scene=0.01, c1_deti_scene=0.01,
                                              c2_dnti_scene=10, c2_deti_scene=10, use_prose_branch=prose)
                    rs = replicar_second_pass(nti, d["eti"], h, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5, c2_deti=5,
                                              is_summit=dist <= 5, c1_dnti_scene=0.01, c1_deti_scene=0.01,
                                              c2_dnti_scene=10, c2_deti_scene=10, use_prose_branch=prose)
                    igual2 = bool(np.array_equal(sp, rs["out"]))
                    fallas += not igual2
                    if not igual2:
                        print("  SEGUNDO PASE DIFIERE")
    # control positivo de la compuerta: con BT fria el centro cae solo por la compuerta
    nti, nti_app, bt, roi, dist = escena(0, frio_bt=True)
    con = first_pass_tests_2_and_3(nti, nti_app, bt, roi, dist, 272.0, 3.0, use_prose_branch=True, **kw)[0][40, 40]
    sin = first_pass_tests_2_and_3(nti, nti_app, bt, roi, dist, 272.0, 3.0, use_prose_branch=True,
                                   apply_bt_gate=False, **kw)[0][40, 40]
    print(f"CONTROL compuerta: BT fria, centro con compuerta={bool(con)} sin compuerta={bool(sin)} (esperado False True)")
    fallas += not ((not con) and sin)
    print("FALLAS:", fallas)
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
