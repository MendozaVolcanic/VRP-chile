# -*- coding: utf-8 -*-
"""Verificador D-42, vuelta 3, afirmacion 5: ¿por que con noches desiguales (11 discordantes en 10 noches, 8 en 7) la
calibracion de P2 cae en 4,9 a 6,7 % por cola aunque todas las contribuciones vayan del mismo lado?

Con la funcion REAL (decidir_p2_bloques del evaluador de hoy) y ademas con una ENUMERACION EXACTA de los 2^B signos
por bloque (B = 7 y 10, o sea 128 y 1.024 asignaciones), aplicando la misma matriz W (pesos_bloque, 10.000, semilla
157) y regla_p2 a cada asignacion. Eso da la tasa exacta de sorteos que caen en cada cola, sin el ruido de los 1.000
sorteos de la calibracion. Y se compara con el valor-p exacto de la prueba de signos por bloque (fraccion de
asignaciones con neto >= observado), que es lo que decidiria «P2 directamente con la prueba de sorteo por bloques».

Pregunta 1 (¿veria una regla rota?): con bloques IGUALES (10 x 1, 7 x 1) la tasa exacta tiene que ser 2^(1-B) por cola
(todos del mismo lado); si con un bloque doble sube a 5 a 7 %, el mecanismo es el peso desigual. Pregunta 2 (¿veria un
instrumento muerto?): la suma de categorias por asignacion es 2^B y el caso de 12 noches iguales decide (control).
Uso: python v21_noches_desiguales.py
"""
import collections
import itertools
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402


def contrib(tam, signo=+1, vol="Lascar"):
    out = []
    for n, t in enumerate(tam):
        for j in range(t):
            out.append({"clave": "%s|VIIRS375|2026-09-%02d 05:%02d" % (vol, n + 1, j), "c": signo,
                        "bloque": "%s|2026-09-%02d" % (vol, n + 1)})
    return out


def exacto(tam):
    """Enumera los 2^B signos por bloque sobre |c| = 1: fraccion de asignaciones con GANA / PIERDE segun regla_p2 con la
    W real, y el valor-p exacto de signos (neto >= observado = sum(tam), a una cola, y a dos colas)."""
    c = contrib(tam)
    bl = [x["bloque"] for x in c]
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    W = np.asarray(X.pesos_bloque(bl), dtype=np.float64)
    a = np.ones(len(c))
    cuenta = collections.Counter()
    netos = []
    for signos in itertools.product((-1.0, 1.0), repeat=len(uniq)):
        s = np.array(signos)[idx]
        cc = s * a
        v = X.regla_p2(W @ cc, int(round(cc.sum())))[0]
        cuenta[v] += 1
        netos.append(cc.sum())
    tot = 2 ** len(uniq)
    obs = float(sum(tam))
    p1 = sum(1 for n in netos if n >= obs) / tot
    p2 = sum(1 for n in netos if abs(n) >= obs) / tot
    return tot, cuenta, p1, p2


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("decidir_p2_bloques de %s | calibracion %d sorteos, semilla %d, tope %.2f" % (
        X.__file__, X.N_CALIB_P2, X.SEMILLA_CALIB_P2, X.MAX_FALSOS_CALIB))
    casos = [("10 noches x 1 (iguales), todas +1", [1] * 10), ("11 en 10 noches (una doble), todas +1", [2] + [1] * 9),
             ("7 noches x 1 (iguales), todas +1", [1] * 7), ("8 en 7 noches (una doble), todas +1", [2] + [1] * 6),
             ("9 en 7 noches (una triple), todas +1", [3] + [1] * 6), ("12 en 10 noches (dos dobles), todas +1", [2, 2] + [1] * 8),
             ("6 noches x 1 (iguales), todas +1", [1] * 6), ("5 noches x 1 (iguales), todas +1", [1] * 5),
             ("12 noches x 1 (iguales), todas +1 (control)", [1] * 12)]
    for nombre, tam in casos:
        v, det = X.decidir_p2_bloques(contrib(tam), ok_ctrl=True)
        tot, cuenta, p1, p2 = exacto(tam)
        print("%-48s REAL: %-12s sin calibrar %-7s falsos GANA %.3f PIERDE %.3f ic95 %s | EXACTO sobre %4d signos: GANA %.4f PIERDE %.4f "
              "BLOQUEA %.4f EMPATE %.4f | valor-p de signos por bloque: una cola %.4f, dos colas %.4f" % (
                  nombre, v, det["resultado_sin_calibrar"], det["falsos_gana"], det["falsos_pierde"], det["ic95"], tot,
                  cuenta["GANA"] / tot, cuenta["PIERDE"] / tot, cuenta["BLOQUEA"] / tot, cuenta["EMPATE"] / tot, p1, p2), flush=True)


if __name__ == "__main__":
    main()
