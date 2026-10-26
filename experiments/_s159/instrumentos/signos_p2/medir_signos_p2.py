# -*- coding: utf-8 -*-
"""S161, D-45 §7 (ADENDA_SIGNOS_P2.md): lo que se mide antes del tag, sin datos reales, con la función REAL
decidir_p2_bloques del evaluador y la regla nueva (D-45) al lado de la de D-42 (que ahora sólo informa, en
det["resultado_d42"]) y de la de D-34 sin calibrar (det["resultado_sin_calibrar"]).

Subcomandos:
  bpm           tasa EXACTA de falsos por cola para B de 5 a 20 con bloques de suma ±1. Bajo el nulo, con bloques de
                magnitud 1 el veredicto depende sólo de cuántos bloques salen +1 (k): se llama a la función real una vez
                por k, con todos los informes, y se pondera por C(B, k) / 2^B. Control de esa afirmación: para B de 5
                a 14 se recorren además los 2^B repartos uno por uno (con informar_d34_d42 apagado sólo para ganar
                tiempo: no decide) y el conteo tiene que ser el mismo.
  enumerables   los nulos de calib_p2/exacto_p2.py que se pueden enumerar (B2, B4 a B9), todas las combinaciones, con
                D-45, D-42 y D-34 sin calibrar.
  escenarios N [lista]   los escenarios nulos y de efecto de V34-01 y de calib_p2/cobertura_p2_calibrada.py (mismos
                generadores, semillas 0..N-1), con D-45 al lado de D-42 y de D-34; intervalos de Wilson al 95 %.
  esperado_escenarios N lista   en los escenarios NULOS, la tasa exacta de D-45 sobre las magnitudes de cada conjunto
                (sin el ruido de los signos sorteados con las semillas 0..N-1).
  v4220         el caso de V42-20: 7 noches del mismo lado decide (p = 1/128), 6 contra 1 no (p = 8/128).

Las dos preguntas del instrumento: (1) ¿vería una regla mal calibrada? Sí: la columna de D-34 sin calibrar reproduce
las tasas que midió el verificador (B = 7: 6,25 % por cola) y en bpm cualquier B con tasa sobre 5 % sale marcado; (2)
¿vería un instrumento muerto? Sí: los escenarios de efecto grande tienen que decidir, y en bpm las probabilidades de
los veredictos suman 1 en cada B.
Uso: python medir_signos_p2.py <subcomando> [args]
"""
import collections
import itertools
import math
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

CAT = ("GANA", "PIERDE", "BLOQUEA", "EMPATE", "SIN SUSTRATO", "INDECIDIBLE")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def fmt(k, n):
    lo, hi = wilson(k, n)
    return "%.3f [%.3f, %.3f]" % (k / n, lo, hi)


def contrib(por_noche, vol="Lascar"):
    out = []
    for n, cs in enumerate(por_noche):
        dia = "2026-%02d-%02d" % (8 + n // 28, 1 + n % 28)
        for j, c in enumerate(cs):
            out.append({"clave": "%s|VIIRS375|%s 05:%02d" % (vol, dia, j), "c": int(c), "bloque": "%s|%s" % (vol, dia)})
    return out


def bpm():
    print("decidir_p2_bloques de %s | exacto hasta B = %d | SIN SUSTRATO con B <= %d | tope 1/%d por cola" % (
        X.__file__, X.MAX_B_EXACTO_P2, X.MAX_B_SIN_SUSTRATO_P2, X.TOPE_P2_DEN))
    print("B | falsos GANA D-45 (exacto) | falsos PIERDE D-45 | ¿<= 5 %? | D-34 sin calibrar GANA / PIERDE (k representativo) "
          "| D-42 GANA / PIERDE (k representativo) | min k que decide PIERDE | p de ese k | control 2^B uno por uno")
    original = X.informar_d34_d42
    for B in range(5, 21):
        t0 = time.time()
        cuenta = {r: collections.Counter() for r in ("d45", "d34", "d42")}
        k_min, p_kmin = None, None
        for k in range(B + 1):
            v, det = X.decidir_p2_bloques(contrib([[+1]] * k + [[-1]] * (B - k)), ok_ctrl=True)
            w = math.comb(B, k)
            cuenta["d45"][v] += w
            cuenta["d34"][det["resultado_sin_calibrar"]] += w
            cuenta["d42"][det["resultado_d42"]] += w
            if v == "PIERDE" and k_min is None:
                k_min, p_kmin = k, Fraction(*det["p_pierde_fraccion"])
        tot = 2 ** B
        assert sum(cuenta["d45"].values()) == tot
        control = "no se corre (B > 14)"
        if B <= 14:
            X.informar_d34_d42 = lambda c, bl, neto, ok: {}
            try:
                uno = collections.Counter()
                for signos in itertools.product((-1, 1), repeat=B):
                    uno[X.decidir_p2_bloques(contrib([[s] for s in signos]), ok_ctrl=True)[0]] += 1
            finally:
                X.informar_d34_d42 = original
            control = "IGUAL" if uno == cuenta["d45"] else "DISTINTO %s" % dict(uno)
        g, p = Fraction(cuenta["d45"]["GANA"], tot), Fraction(cuenta["d45"]["PIERDE"], tot)
        print("%2d | %.5f (%d/%d) | %.5f (%d/%d) | %s | %.4f / %.4f | %.4f / %.4f | %s | %s | %s | %.0fs" % (
            B, float(g), cuenta["d45"]["GANA"], tot, float(p), cuenta["d45"]["PIERDE"], tot,
            "SÍ" if max(g, p) <= Fraction(1, 20) else "NO, SOBRE 5 %",
            cuenta["d34"]["GANA"] / tot, cuenta["d34"]["PIERDE"] / tot, cuenta["d42"]["GANA"] / tot,
            cuenta["d42"]["PIERDE"] / tot, k_min, p_kmin, control, time.time() - t0), flush=True)


def escenario_exacto(nombre, tam, por_noche):
    m = len(tam) if por_noche else sum(tam)
    c45, c42, c34 = collections.Counter(), collections.Counter(), collections.Counter()
    for signos in itertools.product((-1, 1), repeat=m):
        if por_noche:
            pn = [[s] * t for s, t in zip(signos, tam)]
        else:
            it = iter(signos)
            pn = [[next(it) for _ in range(t)] for t in tam]
        v, det = X.decidir_p2_bloques(contrib(pn), ok_ctrl=True)
        c45[v] += 1
        c42[det["resultado_d42"]] += 1
        c34[det["resultado_sin_calibrar"]] += 1
    tot = 2 ** m
    f = lambda c, k: "%.4f" % (c[k] / tot)  # noqa: E731
    print("%-40s %5d comb. | D-45 GANA %s PIERDE %s BLOQUEA %s EMPATE %s SIN SUSTRATO %s | D-42 GANA %s PIERDE %s "
          "INDECIDIBLE %s | D-34 GANA %s PIERDE %s | D-45 %s" % (
              nombre, tot, f(c45, "GANA"), f(c45, "PIERDE"), f(c45, "BLOQUEA"), f(c45, "EMPATE"), f(c45, "SIN SUSTRATO"),
              f(c42, "GANA"), f(c42, "PIERDE"), f(c42, "INDECIDIBLE"), f(c34, "GANA"), f(c34, "PIERDE"),
              "CUMPLE 5 % por cola" if max(c45["GANA"], c45["PIERDE"]) * 20 <= tot else "NO CUMPLE"), flush=True)


def enumerables():
    print("decidir_p2_bloques de %s (nulos enumerables de calib_p2/exacto_p2.py)" % X.__file__)
    escenario_exacto("B2 signo por noche, 6 noches x 6", [6] * 6, True)
    escenario_exacto("B4 iid en el borde, 2+2+1 pasadas", [2, 2, 1], False)
    escenario_exacto("B5 signo por noche, 3 noches x 2", [2] * 3, True)
    escenario_exacto("B6 signo por noche, 4 noches x 2", [2] * 4, True)
    escenario_exacto("B7 signo por noche, 5 noches x 2", [2] * 5, True)
    escenario_exacto("B8 signo por noche, 8 noches x 2", [2] * 8, True)
    escenario_exacto("B9 iid, 5 noches x 2", [2] * 5, False)


ESC = {
    "A": ("A nulo iid (12 noches x 3 pasadas, p=0.5)", "nulo", lambda r: [r.choice((-1, 1), size=3) for _ in range(12)]),
    "B": ("B nulo con signo comun por noche (12 noches x 4 pasadas)", "nulo", lambda r: [[r.choice((-1, 1))] * 4 for _ in range(12)]),
    "B2": ("B2 nulo signo comun por noche (6 noches x 6 pasadas)", "nulo", lambda r: [[r.choice((-1, 1))] * 6 for _ in range(6)]),
    "B3": ("B3 nulo iid, noches desiguales (1 noche x 10 + 9 noches x 1)", "nulo",
           lambda r: [list(r.choice((-1, 1), size=10))] + [[r.choice((-1, 1))] for _ in range(9)]),
    "B4": ("B4 nulo iid en el borde (3 noches: 2+2+1 pasadas)", "nulo",
           lambda r: [list(r.choice((-1, 1), size=2)), list(r.choice((-1, 1), size=2)), [r.choice((-1, 1))]]),
    "B5": ("B5 nulo signo comun por noche en el borde (3 noches x 2)", "nulo", lambda r: [[r.choice((-1, 1))] * 2 for _ in range(3)]),
    "B6": ("B6 nulo signo comun por noche (4 noches x 2)", "nulo", lambda r: [[r.choice((-1, 1))] * 2 for _ in range(4)]),
    "B7": ("B7 nulo signo comun por noche (5 noches x 2)", "nulo", lambda r: [[r.choice((-1, 1))] * 2 for _ in range(5)]),
    "B8": ("B8 nulo signo comun por noche (8 noches x 2)", "nulo", lambda r: [[r.choice((-1, 1))] * 2 for _ in range(8)]),
    "C": ("C efecto grande a favor de D (p(-1)=0.85, 12 noches x 3)", "efecto",
          lambda r: [r.choice((-1, 1), size=3, p=(0.85, 0.15)) for _ in range(12)]),
    "C2": ("C2 efecto grande en contra de D (p(+1)=0.85, 12 noches x 3)", "efecto",
           lambda r: [r.choice((-1, 1), size=3, p=(0.15, 0.85)) for _ in range(12)]),
    "D": ("D efecto moderado a favor (p(-1)=0.70, 20 noches x 2)", "efecto",
          lambda r: [r.choice((-1, 1), size=2, p=(0.70, 0.30)) for _ in range(20)]),
    "E": ("E efecto por noche (noche entera a favor con p=0.8, 10 x 4)", "efecto",
          lambda r: [[r.choice((-1, 1), p=(0.8, 0.2))] * 4 for _ in range(10)]),
    "F": ("F efecto grande con pocas noches (p(-1)=0.85, 4 noches x 3)", "efecto",
          lambda r: [r.choice((-1, 1), size=3, p=(0.85, 0.15)) for _ in range(4)]),
    "F2": ("F2 efecto total con pocas noches (todas a favor, 5 noches x 2)", "efecto", lambda r: [[-1, -1] for _ in range(5)]),
}


def escenarios(n_sim, solo):
    print("decidir_p2_bloques de %s | D-45: semilla %d, %d sorteos con B > %d | D-42 (informa): %d sorteos, semilla %d" % (
        X.__file__, X.SEMILLA_P2_SIGNOS, X.N_SORTEOS_P2_SIGNOS, X.MAX_B_EXACTO_P2, X.N_CALIB_P2, X.SEMILLA_CALIB_P2))
    for clave in solo:
        nombre, tipo, gen = ESC[clave]
        t0 = time.time()
        c = {r: collections.Counter() for r in ("D-45", "D-42", "D-34")}
        for s in range(n_sim):
            v, det = X.decidir_p2_bloques(contrib(gen(np.random.default_rng(s))), ok_ctrl=True)
            c["D-45"][v] += 1
            c["D-42"][det["resultado_d42"]] += 1
            c["D-34"][det["resultado_sin_calibrar"]] += 1
        print("%-62s n=%d | %s" % (nombre, n_sim, "NULO: GANA y PIERDE son falsos" if tipo == "nulo" else "EFECTO: poder"))
        for r in ("D-45", "D-42", "D-34"):
            print("   %-5s %s | %.0fs" % (r, " | ".join("%s %s" % (k, fmt(c[r][k], n_sim)) for k in CAT if c[r][k] or k in
                                                       ("GANA", "PIERDE")), time.time() - t0), flush=True)


def esperado_escenarios(n_sim, solo):
    """Separa la regla de la muestra de semillas: para cada conjunto de un escenario NULO (semillas 0..n-1, los mismos
    que escenarios), la probabilidad EXACTA de que D-45 decida GANA o PIERDE si los signos de sus bloques se sortearan
    de nuevo (2^B repartos, prueba_signos_p2 y regla_signos_p2 reales, una llamada por neto posible). En los nulos de
    estos generadores, dada la magnitud de cada bloque su signo es simétrico e independiente (iid por pasada o signo
    común por noche), así que el promedio es la tasa de la regla sobre esas magnitudes sin el ruido de los signos
    sorteados. Con B > 20 se usa el valor-p exacto en vez del de sorteos (aproximación, marcada)."""
    for clave in solo:
        nombre, tipo, gen = ESC[clave]
        eg = ep = 0.0
        aprox = 0
        for s in range(n_sim):
            c = contrib(gen(np.random.default_rng(s)))
            tot = collections.Counter()
            for x in c:
                tot[x["bloque"]] += x["c"]
            mags = [abs(v) for v in tot.values()]
            B = len(mags)
            aprox += B > X.MAX_B_EXACTO_P2
            dist = {0: 1}
            for m in mags:
                nueva = collections.Counter()
                for v, k in dist.items():
                    nueva[v + m] += k
                    nueva[v - m] += k
                dist = nueva
            den = 2 ** B
            for neto, k in dist.items():
                pr = X.prueba_signos_p2(mags, neto) if B <= X.MAX_B_EXACTO_P2 else {
                    "gana": [sum(q for x, q in dist.items() if x <= neto), den],
                    "pierde": [sum(q for x, q in dist.items() if x >= neto), den]}
                v = X.regla_signos_p2(neto, B, pr)
                eg += k / den * (v == "GANA")
                ep += k / den * (v == "PIERDE")
        print("%-62s n=%d | D-45 esperado exacto sobre estas magnitudes: GANA %.4f, PIERDE %.4f%s" % (
            nombre, n_sim, eg / n_sim, ep / n_sim, " (aproximado en %d conjuntos con B > 20)" % aprox if aprox else ""),
            flush=True)


def v4220():
    for por_noche, nombre in (([[+1]] * 7, "7 noches de +1"), ([[-1]] * 7, "7 noches de -1"),
                              ([[+1]] * 6 + [[-1]], "6 de +1 contra 1 de -1"), ([[-1]] * 6 + [[+1]], "6 de -1 contra 1 de +1")):
        v, det = X.decidir_p2_bloques(contrib(por_noche), ok_ctrl=True)
        print("%-24s D-45 %-8s p GANA %s PIERDE %s dos colas %s (%s) | D-34 %s IC95 %s | D-42 %s (falsos GANA %.3f, PIERDE %.3f)" % (
            nombre, v, Fraction(*det["p_gana_fraccion"]), Fraction(*det["p_pierde_fraccion"]),
            Fraction(*det["p_dos_colas_fraccion"]), det["metodo"], det["resultado_sin_calibrar"], det["ic95"],
            det["resultado_d42"], det["falsos_gana"], det["falsos_pierde"]))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "bpm":
        bpm()
    elif cmd == "enumerables":
        enumerables()
    elif cmd == "escenarios":
        escenarios(int(sys.argv[2]), sys.argv[3].split(",") if len(sys.argv) > 3 else list(ESC))
    elif cmd == "esperado_escenarios":
        esperado_escenarios(int(sys.argv[2]), sys.argv[3].split(","))
    elif cmd == "v4220":
        v4220()
