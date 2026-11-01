# -*- coding: utf-8 -*-
"""S162 instrumento T3: el port de M (D-27, D-28, D-30, D-32) y de P2 (D-45) en scripts/evaluador_comun.py da
EXACTAMENTE lo mismo que experiments/_s157_prereg_d25/evaluar_d25.py del tag s161-d25-lectura (blob 1dbabf657).

Sobre pares sintéticos al azar de varios tamaños y efectos (incluidos el placebo D = K×g y casos sin sustrato), compara
decidir_estrato (modo decide, bloquea e informa, calibración simétrica) y la prueba de signos de P2, campo por campo.
El original se importa sólo para leer (python -B, sin escribir __pycache__) desde su worktree.
Uso: python -B -I experiments/_s162_instrumento/t3_equivalencia.py <dir del evaluador sellado> [--control-negativo]
     (p. ej. C:/vrp-trabajo/s159-evaluador/experiments/_s157_prereg_d25)
"""
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
from scripts import evaluador_comun as N  # noqa: E402

sys.path.insert(0, sys.argv[1])
import evaluar_d25 as O  # noqa: E402

assert (O.N_BOOT, O.SEMILLA, O.N_CALIB, O.MAX_FALSOS_CALIB, O.SEMILLA_CALIB_DPRIMA, O.N_CALIB_DPRIMA, O.DEC_DPRIMA,
        O.MIN_VOLCANES_MEJORA, O.MIN_PARES_VOLCAN, O.N_MIN_PARES, O.N_MIN_NOCHES, O.SEMILLA_P2_SIGNOS,
        O.N_SORTEOS_P2_SIGNOS, O.MAX_B_EXACTO_P2, O.MAX_B_SIN_SUSTRATO_P2, O.TOPE_P2_DEN, O.PLACEBO_GANANCIAS) == (
        N.N_BOOT, N.SEMILLA, N.N_CALIB, N.MAX_FALSOS_CALIB, N.SEMILLA_CALIB_DPRIMA, N.N_CALIB_DPRIMA, N.DEC_DPRIMA,
        N.MIN_VOLCANES_MEJORA, N.MIN_PARES_VOLCAN, N.N_MIN_PARES, N.N_MIN_NOCHES, N.SEMILLA_P2_SIGNOS,
        N.N_SORTEOS_P2_SIGNOS, N.MAX_B_EXACTO_P2, N.MAX_B_SIN_SUSTRATO_P2, N.TOPE_P2_DEN, N.PLACEBO_GANANCIAS)

VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Villarrica", "PuyehueCordonCaulle"]
# Control negativo del instrumento (A110): con --control-negativo el port usa otra semilla para calibrar d′ y exige un
# volcán más para el MEJORA; el script TIENE que encontrar diferencias. Si no las encuentra, el 0 de arriba no vale.
CONTROL_NEGATIVO = "--control-negativo" in sys.argv
if CONTROL_NEGATIVO:
    N.SEMILLA_CALIB_DPRIMA = N.SEMILLA_CALIB_DPRIMA + 1000
    N.MIN_VOLCANES_MEJORA = N.MIN_VOLCANES_MEJORA + 1


def pares(rng, n, efecto, ruido, ganancia=None):
    P = []
    for i in range(n):
        v = rng.choice(VOLS); dia = "2026-10-%02d" % rng.randint(1, 20)
        m = 10 ** rng.uniform(-1.5, 1.2)
        k = m * 10 ** rng.gauss(-0.25, 0.25)
        d = k * ganancia if ganancia else k * 10 ** (efecto + rng.gauss(0, ruido))
        P.append({"k": k, "d": d, "m": m, "clave": "%s|VIIRS750|%s 05:%02d" % (v, dia, i % 60), "bloque": "%s|%s" % (v, dia)})
    return P


def limpio(x):
    return json.loads(json.dumps(x, default=float))


rng = random.Random(20261024)
casos = 0
dif = []
for n in ((12, 25) if CONTROL_NEGATIVO else (3, 6, 12, 25, 60)):
    for efecto, ruido, gan in ((0.0, 0.2, None), (0.12, 0.1, None), (-0.12, 0.1, None), (0.0, 0.0, 1.2), (0.0, 0.0, 0.8),
                               (0.05, 0.3, None)):
        P = pares(rng, n, efecto, ruido, gan)
        for modo in ("decide", "bloquea", "informa"):
            casos += 1
            if len(P) < O.N_MIN_PARES or len({p["bloque"] for p in P}) < O.N_MIN_NOCHES:
                ro = ("SIN SUSTRATO", None)
            else:
                ro = O.decidir_estrato(P, modo, "simetrica", True)
            rn = N.decidir_estrato(P, modo)
            a, b = limpio(ro), limpio(rn)
            if ro[1] is None:
                a, b = a[0], b[0]
            else:
                a[1].pop("modo_calibracion", None)
            if a != b:
                dif.append((n, efecto, gan, modo, a, b))
# P2: prueba de signos sobre sumas de bloque al azar, exacta y por sorteos
for B in (1, 4, 5, 7, 12, 20, 21, 35):
    for _ in range(20):
        sumas = [rng.choice((-2, -1, -1, 0, 1, 1, 2)) for _ in range(B)]
        neto = sum(sumas)
        casos += 1
        po, pn = O.prueba_signos_p2(sumas, neto), N.prueba_signos_p2(sumas, neto)
        for k in ("metodo", "gana", "pierde", "dos_colas", "minimo"):
            if po[k] != pn[k]:
                dif.append(("P2", B, sumas, k, po[k], pn[k]))
        if O.regla_signos_p2(neto, B, po) != N.regla_signos_p2(neto, B, pn):
            dif.append(("regla P2", B, sumas))
print("control negativo (port perturbado):" if CONTROL_NEGATIVO else "port tal cual:", "casos comparados:", casos)
print("diferencias:", len(dif))
for d in dif[:10]:
    print("  ", d)
sys.exit((0 if dif else 1) if CONTROL_NEGATIVO else (1 if dif else 0))
