# -*- coding: utf-8 -*-
"""Verificador de la adenda K, pregunta 4: la opcion A (G1 cumple si P(nulo >= D) < 0,05 con el nulo exacto).

Implementacion PROPIA del nulo exacto (no copia la del verificador de W2 a W6): la convolucion se hace sobre la
pmf entera de cada estrato con una hipergeometrica escrita a mano con math.comb (no scipy), para que un error comun
con scipy.stats.hypergeom no pase como acuerdo. Cuatro cosas:
  1. fuerza bruta: en estratos chicos se enumeran TODOS los repartos de etiquetas y se compara con la convolucion;
  2. sobre las clases de la corrida C0 (resultado.json), los valores del verificador (0,5223 / 0,1058 / 0,0253,
     cuantil +0,2760 y +0,2303);
  3. la regla A contra la regla vigente (D > p95 + EPS) y contra «D > cuantil 95 exacto»: en que se distinguen;
  4. el muestreo del evaluador (ED.nulo_barajado, 10.000) contra el exacto, en cola (P(nulo >= D)) y en cuantil.
Uso: python -I p4_cuantil_exacto.py <resultado.json de W2_W6_s154>
"""
import collections
import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import evaluar_diurno as ED  # noqa: E402


def pmf_hiper(n, k, p):
    """X = publicadas entre las p positivas de un estrato de n con k publicadas. Exacto con Fraction."""
    tot = math.comb(n, p)
    return [Fraction(math.comb(k, x) * math.comb(n - k, p - x), tot) for x in range(0, min(p, k) + 1)]


def convol(estratos):
    pmf = [Fraction(1)]
    for n, p, k in estratos:
        f = pmf_hiper(n, k, p)
        out = [Fraction(0)] * (len(pmf) + len(f) - 1)
        for i, a in enumerate(pmf):
            if a:
                for j, b in enumerate(f):
                    if b:
                        out[i + j] += a * b
        pmf = out
    return pmf


def fuerza_bruta(estratos):
    """Enumera todas las asignaciones de las p positivas entre las n pasadas de cada estrato."""
    por_estrato = []
    for n, p, k in estratos:
        c = collections.Counter()
        pub = [1] * k + [0] * (n - k)
        for pos in itertools.combinations(range(n), p):
            c[sum(pub[i] for i in pos)] += 1
        tot = sum(c.values())
        por_estrato.append({x: Fraction(v, tot) for x, v in c.items()})
    out = collections.Counter()
    for combo in itertools.product(*[list(d.items()) for d in por_estrato]):
        x = sum(t[0] for t in combo)
        pr = Fraction(1)
        for t in combo:
            pr *= t[1]
        out[x] += pr
    m = max(out)
    return [out.get(x, Fraction(0)) for x in range(m + 1)]


def estratos_y_xobs(clases, ventanas):
    est = collections.defaultdict(lambda: [0, 0, 0])
    xobs = 0
    for clave, c in clases.items():
        vol, sen, _ = clave.split("|")
        pob = set(c["pob"])
        if c["ventana"] not in ventanas or c["estado"] == "no_procesada" or not ({"pos", "neg"} & pob):
            continue
        e = est[(vol, sen)]
        e[0] += 1
        e[1] += "pos" in pob
        pub = c["estado"] == "publicada"
        e[2] += pub
        xobs += ("pos" in pob) and pub
        if {"pos", "neg"} <= pob:
            print("   AVISO: pasada a la vez pos y neg:", clave)
    return [tuple(est[k]) for k in sorted(est)], xobs


def main(ruta):
    print("== 1. fuerza bruta contra convolucion (estratos chicos, Fraction exacta)")
    rng = np.random.default_rng(7)
    malos = 0
    for t in range(200):
        est = []
        for _ in range(rng.integers(1, 4)):
            n = int(rng.integers(1, 9)); p = int(rng.integers(0, n + 1)); k = int(rng.integers(0, n + 1))
            est.append((n, p, k))
        a, b = convol(est), fuerza_bruta(est)
        L = max(len(a), len(b)); a += [Fraction(0)] * (L - len(a)); b += [Fraction(0)] * (L - len(b))
        malos += a != b
    print("   200 casos al azar: %d distintos" % malos)

    clases = json.load(open(ruta, encoding="utf-8"))["clases"]
    print("\n== 2. clases de la corrida C0 (%d pasadas)" % len(clases))
    for nom, ws in (("W2 a W6", ED.DECIDEN), ("W3 a W6", ED.SIN_W2)):
        est, xobs = estratos_y_xobs(clases, ws)
        P = sum(e[1] for e in est); N = sum(e[0] - e[1] for e in est); K = sum(e[2] for e in est)
        pmf = convol(est)
        assert sum(pmf) == 1
        D = [Fraction(x, P) - Fraction(K - x, N) for x in range(len(pmf))]
        dobs = Fraction(xobs, P) - Fraction(K - xobs, N)
        ge = sum(pmf[xobs:]); gt = sum(pmf[xobs + 1:])
        cdf = list(itertools.accumulate(pmf))
        q95x = next(x for x, c in enumerate(cdf) if c >= Fraction(95, 100))
        # regla vigente aplicada al exacto: D > q95 ; regla A: P(nulo >= D) < 0,05
        print("   %s: P %d N %d K %d X_obs %d D %+.4f | P(>=D) %.4f P(>D) %.4f | cuantil95 exacto X=%d D %+.4f"
              % (nom, P, N, K, xobs, float(dobs), float(ge), float(gt), q95x, float(D[q95x])))
        print("      regla A (P(>=D) < 0,05): %s | D > cuantil95 exacto: %s | el X minimo que cumple A: X=%d (D %+.4f, P(>=) %.4f)"
              % ("CUMPLE" if ge < Fraction(5, 100) else "FALLA", "CUMPLE" if dobs > D[q95x] else "FALLA",
                 next(x for x in range(len(pmf)) if sum(pmf[x:]) < Fraction(5, 100)),
                 float(D[next(x for x in range(len(pmf)) if sum(pmf[x:]) < Fraction(5, 100))]),
                 float(sum(pmf[next(x for x in range(len(pmf)) if sum(pmf[x:]) < Fraction(5, 100)):]))))
        # tamano real de la prueba A bajo el nulo
        xa = next(x for x in range(len(pmf)) if sum(pmf[x:]) < Fraction(5, 100))
        print("      tamano real de la regla A bajo el nulo: P(cumplir por azar) = %.4f (nominal 0,05)" % float(sum(pmf[xa:])))
        # 4. muestreo del evaluador contra exacto
        r = []
        for semilla in range(20):
            nul = ED.nulo_barajado(est, np.random.default_rng(semilla))
            r.append((float(np.mean(nul >= float(dobs) - 1e-12)), float(np.percentile(nul, 95))))
        cola = [x[0] for x in r]; p95s = sorted({round(x[1], 4) for x in r})
        se = math.sqrt(float(ge) * (1 - float(ge)) / ED.N_BARAJADOS)
        print("   4. muestreo 10.000 x 20 semillas: P(>=D) muestreada %.4f a %.4f (exacta %.4f, 3 EE = %.4f) | p95 muestreado toma %s"
              % (min(cola), max(cola), float(ge), 3 * se, p95s))
        # D en flotante del evaluador contra el D del atomo X_obs en flotante
        d_eval = xobs / P - (K - xobs) / N
        print("      D del evaluador en float == atomo X_obs del nulo en float: %s" % (d_eval == (np.array([xobs]) / P - (K - np.array([xobs])) / N)[0]))


if __name__ == "__main__":
    main(sys.argv[1])
