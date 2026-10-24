# -*- coding: utf-8 -*-
"""Verificador D-34: cobertura del intervalo de P2 (decidir_p2_bloques) con datos sinteticos propios.

Las dos preguntas del instrumento:
1. Si el bootstrap por bloques estuviera roto (p. ej. remuestreara por pasada), esta medicion lo veria? Si: el
   escenario B (signo comun por noche) infla la tasa de falsas decisiones si el remuestreo ignora la noche, y se mide
   ademas con pesos_pasada como control positivo del instrumento.
2. Si el instrumento estuviera muerto, el resultado se veria distinto? Si: el escenario C (efecto grande) tiene que
   decidir GANA casi siempre; un instrumento muerto daria EMPATE o SIN SUSTRATO en todo.

Denominadores: N_SIM conjuntos sinteticos por escenario, semillas 0..N_SIM-1 del generador propio; cada conjunto
decide con la funcion REAL del evaluador (10.000 remuestreos, semilla 157, la de M). No se toca ningun dato real.
"""
import collections
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

N_SIM = int(sys.argv[1]) if len(sys.argv) > 1 else 400
SOLO = sys.argv[2].split(',') if len(sys.argv) > 2 else None


def contrib(signos_por_noche, vol="Lascar"):
    out = []
    for n, cs in enumerate(signos_por_noche):
        for j, c in enumerate(cs):
            out.append({"clave": "%s|VIIRS375|2026-09-%02d 05:%02d" % (vol, n + 1, j), "c": int(c),
                        "bloque": "%s|2026-09-%02d" % (vol, n + 1)})
    return out


def decidir_por_pasada(contrib_):
    """La misma regla pero con remuestreo por PASADA (pesos_pasada): control positivo del instrumento, no la regla."""
    c = np.array([x["c"] for x in contrib_], dtype=np.float64)
    W = X.pesos_pasada(len(c))
    sumas = W @ c
    lo, hi = float(np.percentile(sumas, 2.5)), float(np.percentile(sumas, 97.5))
    neto = int(round(c.sum()))
    return "GANA" if hi < 0 else "PIERDE" if lo > 0 else "BLOQUEA" if neto > 0 else "EMPATE"


def escenario(nombre, gen, por_pasada=False):
    if SOLO and nombre.split()[0] not in SOLO:
        return None
    t0 = time.time()
    cnt, cnt_pp = collections.Counter(), collections.Counter()
    for s in range(N_SIM):
        rng = np.random.default_rng(s)
        c = contrib(gen(rng))
        v, _ = X.decidir_p2_bloques(c, ok_ctrl=True)
        cnt[v] += 1
        if por_pasada:
            cnt_pp[decidir_por_pasada(c)] += 1
    dec = cnt["GANA"] + cnt["PIERDE"]
    print("%-58s n=%d | GANA %3d PIERDE %3d EMPATE %3d BLOQUEA %3d SIN SUSTRATO %3d | GANA+PIERDE %.3f%s | %.0fs" % (
        nombre, N_SIM, cnt["GANA"], cnt["PIERDE"], cnt["EMPATE"], cnt["BLOQUEA"], cnt["SIN SUSTRATO"], dec / N_SIM,
        (" | por PASADA (control del instrumento): GANA+PIERDE %.3f" % ((cnt_pp["GANA"] + cnt_pp["PIERDE"]) / N_SIM))
        if por_pasada else "", time.time() - t0), flush=True)
    return cnt


def main():
    print("decidir_p2_bloques del evaluador %s | N_BOOT %d SEMILLA %d | minimos %d pasadas / %d noches" % (
        X.__file__, X.N_BOOT, X.SEMILLA, X.N_MIN_PARES, X.N_MIN_NOCHES))
    # A. nulo verdadero, signos independientes por pasada: 12 noches x 3 pasadas
    escenario("A nulo iid (12 noches x 3 pasadas, p=0.5)",
              lambda r: [r.choice((-1, 1), size=3) for _ in range(12)], por_pasada=True)
    # B. nulo verdadero con correlacion intra-noche total: todas las pasadas de una noche comparten signo
    escenario("B nulo con signo comun por noche (12 noches x 4 pasadas)",
              lambda r: [[r.choice((-1, 1))] * 4 for _ in range(12)], por_pasada=True)
    # B2. igual pero pocas noches (6) y muchas pasadas por noche (6): el sustrato minimo de verdad
    escenario("B2 nulo signo comun por noche (6 noches x 6 pasadas)",
              lambda r: [[r.choice((-1, 1))] * 6 for _ in range(6)], por_pasada=True)
    # B3. nulo con tamanos de noche muy desiguales (una noche de 10 pasadas, 9 noches de 1)
    escenario("B3 nulo iid, noches desiguales (1 noche x 10 + 9 noches x 1)",
              lambda r: [list(r.choice((-1, 1), size=10))] + [[r.choice((-1, 1))] for _ in range(9)], por_pasada=True)
    # B4. nulo en el borde del sustrato: 3 noches, 5 pasadas
    escenario("B4 nulo iid en el borde (3 noches: 2+2+1 pasadas)",
              lambda r: [list(r.choice((-1, 1), size=2)), list(r.choice((-1, 1), size=2)), [r.choice((-1, 1))]])
    # B5-B7. nulo con signo comun por noche en el borde del sustrato: con B noches, la probabilidad de que todas
    # caigan del mismo lado es 2^(1-B) y entonces TODO remuestreo queda de ese lado: decide en falso.
    escenario("B5 nulo signo comun por noche en el borde (3 noches x 2)",
              lambda r: [[r.choice((-1, 1))] * 2 for _ in range(3)])
    escenario("B6 nulo signo comun por noche (4 noches x 2)",
              lambda r: [[r.choice((-1, 1))] * 2 for _ in range(4)])
    escenario("B7 nulo signo comun por noche (5 noches x 2)",
              lambda r: [[r.choice((-1, 1))] * 2 for _ in range(5)])
    escenario("B8 nulo signo comun por noche (8 noches x 2)",
              lambda r: [[r.choice((-1, 1))] * 2 for _ in range(8)])
    # C. efecto grande: D comete menos errores en el 85 % de las discordantes, 12 noches x 3
    escenario("C efecto grande a favor de D (p(-1)=0.85, 12 noches x 3)",
              lambda r: [r.choice((-1, 1), size=3, p=(0.85, 0.15)) for _ in range(12)])
    # C2. efecto grande en contra de D
    escenario("C2 efecto grande en contra de D (p(+1)=0.85, 12 noches x 3)",
              lambda r: [r.choice((-1, 1), size=3, p=(0.15, 0.85)) for _ in range(12)])
    # D. efecto moderado, mas noches
    escenario("D efecto moderado a favor (p(-1)=0.70, 20 noches x 2)",
              lambda r: [r.choice((-1, 1), size=2, p=(0.70, 0.30)) for _ in range(20)])
    # E. efecto por noche (toda la noche a favor con p=0.8), 10 noches x 4
    escenario("E efecto por noche (noche entera a favor con p=0.8, 10 x 4)",
              lambda r: [[r.choice((-1, 1), p=(0.8, 0.2))] * 4 for _ in range(10)])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
