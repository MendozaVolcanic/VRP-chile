# -*- coding: utf-8 -*-
"""S160, D-42 §5: falsos GANA y PIERDE de P2 calibrada en los escenarios nulos de V34-01, y su poder en los de efecto.

Reusa los escenarios de experiments/_s159/instrumentos/verificador_d34/cobertura_p2.py (mismos generadores, mismas
semillas 0..n-1 por conjunto), con la función REAL decidir_p2_bloques, que desde D-42 trae la calibración. Cada
conjunto da dos veredictos: el calibrado (el que decide) y el sin calibrar (det["resultado_sin_calibrar"], que es la
regla de D-34 tal cual y sirve de control: tiene que reproducir lo que midió el verificador de D-34).

Las dos preguntas del instrumento:
1. Si la calibración no hiciera nada, ¿se vería? Sí: la columna sin calibrar reproduce el 24,8 % de B5, y la
   calibrada tendría que dar lo mismo.
2. Si el instrumento estuviera muerto, ¿se vería? Sí: los escenarios de efecto grande (C, C2) tienen que decidir; un
   instrumento muerto daría INDECIDIBLE o SIN SUSTRATO en todo.

Denominadores: n conjuntos por escenario (argumento 1), intervalos de Wilson al 95 %. Datos 100 % sintéticos.
Uso: python cobertura_p2_calibrada.py <n> [escenarios separados por coma]
"""
import collections
import math
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

N_SIM = int(sys.argv[1]) if len(sys.argv) > 1 else 400
SOLO = sys.argv[2].split(",") if len(sys.argv) > 2 else None


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def contrib(signos_por_noche, vol="Lascar"):
    out = []
    for n, cs in enumerate(signos_por_noche):
        for j, c in enumerate(cs):
            out.append({"clave": "%s|VIIRS375|2026-09-%02d 05:%02d" % (vol, n + 1, j), "c": int(c),
                        "bloque": "%s|2026-09-%02d" % (vol, n + 1)})
    return out


def fmt(k, n):
    lo, hi = wilson(k, n)
    return "%.3f [%.3f, %.3f]" % (k / n, lo, hi)


def escenario(nombre, tipo, gen):
    if SOLO and nombre.split()[0] not in SOLO:
        return
    t0 = time.time()
    cal, sin = collections.Counter(), collections.Counter()
    for s in range(N_SIM):
        rng = np.random.default_rng(s)
        v, det = X.decidir_p2_bloques(contrib(gen(rng)), ok_ctrl=True)
        cal[v] += 1
        sin[det["resultado_sin_calibrar"]] += 1
    n = N_SIM
    print("%-62s n=%d | %s" % (nombre, n, tipo))
    print("   CALIBRADA   GANA %s | PIERDE %s | INDECIDIBLE %s | BLOQUEA %s | EMPATE %s | SIN SUSTRATO %d" % (
        fmt(cal["GANA"], n), fmt(cal["PIERDE"], n), fmt(cal["INDECIDIBLE"], n), fmt(cal["BLOQUEA"], n),
        fmt(cal["EMPATE"], n), cal["SIN SUSTRATO"]))
    print("   SIN CALIBRAR GANA %s | PIERDE %s | BLOQUEA %s | EMPATE %s | GANA+PIERDE %.3f | %.0fs" % (
        fmt(sin["GANA"], n), fmt(sin["PIERDE"], n), fmt(sin["BLOQUEA"], n), fmt(sin["EMPATE"], n),
        (sin["GANA"] + sin["PIERDE"]) / n, time.time() - t0), flush=True)


def main():
    print("decidir_p2_bloques de %s | N_BOOT %d SEMILLA %d | calibración %d sorteos, semilla %d, tope %.2f por cola" % (
        X.__file__, X.N_BOOT, X.SEMILLA, X.N_CALIB_P2, X.SEMILLA_CALIB_P2, X.MAX_FALSOS_CALIB))
    nulo, ef = "NULO: GANA y PIERDE son falsos", "EFECTO: poder"
    escenario("A nulo iid (12 noches x 3 pasadas, p=0.5)", nulo, lambda r: [r.choice((-1, 1), size=3) for _ in range(12)])
    escenario("B nulo con signo comun por noche (12 noches x 4 pasadas)", nulo, lambda r: [[r.choice((-1, 1))] * 4 for _ in range(12)])
    escenario("B2 nulo signo comun por noche (6 noches x 6 pasadas)", nulo, lambda r: [[r.choice((-1, 1))] * 6 for _ in range(6)])
    escenario("B3 nulo iid, noches desiguales (1 noche x 10 + 9 noches x 1)", nulo,
              lambda r: [list(r.choice((-1, 1), size=10))] + [[r.choice((-1, 1))] for _ in range(9)])
    escenario("B4 nulo iid en el borde (3 noches: 2+2+1 pasadas)", nulo,
              lambda r: [list(r.choice((-1, 1), size=2)), list(r.choice((-1, 1), size=2)), [r.choice((-1, 1))]])
    escenario("B5 nulo signo comun por noche en el borde (3 noches x 2)", nulo, lambda r: [[r.choice((-1, 1))] * 2 for _ in range(3)])
    escenario("B6 nulo signo comun por noche (4 noches x 2)", nulo, lambda r: [[r.choice((-1, 1))] * 2 for _ in range(4)])
    escenario("B7 nulo signo comun por noche (5 noches x 2)", nulo, lambda r: [[r.choice((-1, 1))] * 2 for _ in range(5)])
    escenario("B8 nulo signo comun por noche (8 noches x 2)", nulo, lambda r: [[r.choice((-1, 1))] * 2 for _ in range(8)])
    escenario("C efecto grande a favor de D (p(-1)=0.85, 12 noches x 3)", ef,
              lambda r: [r.choice((-1, 1), size=3, p=(0.85, 0.15)) for _ in range(12)])
    escenario("C2 efecto grande en contra de D (p(+1)=0.85, 12 noches x 3)", ef,
              lambda r: [r.choice((-1, 1), size=3, p=(0.15, 0.85)) for _ in range(12)])
    escenario("D efecto moderado a favor (p(-1)=0.70, 20 noches x 2)", ef,
              lambda r: [r.choice((-1, 1), size=2, p=(0.70, 0.30)) for _ in range(20)])
    escenario("E efecto por noche (noche entera a favor con p=0.8, 10 x 4)", ef,
              lambda r: [[r.choice((-1, 1), p=(0.8, 0.2))] * 4 for _ in range(10)])
    # agregado: efecto grande con pocas noches (donde la calibración puede dejar sin poder a la regla)
    escenario("F efecto grande con pocas noches (p(-1)=0.85, 4 noches x 3)", ef,
              lambda r: [r.choice((-1, 1), size=3, p=(0.85, 0.15)) for _ in range(4)])
    escenario("F2 efecto total con pocas noches (todas a favor, 5 noches x 2)", ef, lambda r: [[-1, -1] for _ in range(5)])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
