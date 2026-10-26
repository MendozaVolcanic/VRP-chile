# -*- coding: utf-8 -*-
"""S160, D-42 §5: tasa EXACTA de falsos GANA y PIERDE de P2 calibrada en los escenarios nulos que se pueden enumerar.

POR QUÉ. cobertura_p2_calibrada.py sortea 500 conjuntos con las semillas 0..499 del generador de V34-01, y esa muestra
no es pareja: en B7 (5 noches) el generador da 30 conjuntos con las cinco noches del mismo lado positivo y 13 del
negativo, contra 15,6 esperados por lado (contado aparte). Como el falso PIERDE de B7 es justamente «todas las noches
positivas», la tasa medida por cola sale inflada por la muestra, no por la regla. Aquí no se sortea: se recorren TODAS
las combinaciones de signos (cada una con probabilidad 2^-m bajo el nulo) y se aplica la función real
decidir_p2_bloques a cada una. El resultado es la probabilidad exacta, sin error de muestreo.

Escenarios: los nulos de V34-01 con 2^m combinaciones manejables (m = signos libres): B2 (6 noches x 6, signo por
noche, 64), B4 (iid, 2+2+1 pasadas, 32), B5 a B8 (signo por noche, 3 a 8 noches de 2 pasadas, 8 a 256), y B9 (iid,
5 noches de 2 pasadas, 1.024). Los de 12 noches (A, B) y B3 quedan con el muestreo (4.096 o más combinaciones).

Las dos preguntas del instrumento: (1) ¿vería una regla mal calibrada? Sí: la columna «sin calibrar» reproduce la
tasa exacta de la regla de D-34 (B5: 2/8 = 25 %); (2) ¿vería un evaluador muerto? Sí: cada combinación da un veredicto
y la suma de probabilidades tiene que ser 1.
Uso: python exacto_p2.py
"""
import collections
import itertools
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402


def contrib(por_noche, vol="Lascar"):
    out = []
    for n, cs in enumerate(por_noche):
        for j, c in enumerate(cs):
            out.append({"clave": "%s|VIIRS375|2026-09-%02d 05:%02d" % (vol, n + 1, j), "c": int(c),
                        "bloque": "%s|2026-09-%02d" % (vol, n + 1)})
    return out


def escenario(nombre, tam, por_noche):
    """tam: tamaños de las noches; por_noche: True si el signo es común a toda la noche, False si es por pasada."""
    m = len(tam) if por_noche else sum(tam)
    cal, sin = collections.Counter(), collections.Counter()
    for signos in itertools.product((-1, 1), repeat=m):
        if por_noche:
            pn = [[s] * t for s, t in zip(signos, tam)]
        else:
            it = iter(signos)
            pn = [[next(it) for _ in range(t)] for t in tam]
        v, det = X.decidir_p2_bloques(contrib(pn), ok_ctrl=True)
        cal[v] += 1
        sin[det["resultado_sin_calibrar"]] += 1
    tot = 2 ** m
    assert sum(cal.values()) == tot
    f = lambda c, k: "%.4f" % (c[k] / tot)  # noqa: E731
    print("%-48s %5d combinaciones | CALIBRADA GANA %s PIERDE %s INDECIDIBLE %s BLOQUEA %s EMPATE %s | SIN CALIBRAR "
          "GANA %s PIERDE %s | %s" % (nombre, tot, f(cal, "GANA"), f(cal, "PIERDE"), f(cal, "INDECIDIBLE"),
                                      f(cal, "BLOQUEA"), f(cal, "EMPATE"), f(sin, "GANA"), f(sin, "PIERDE"),
                                      "CUMPLE 5 % por cola" if max(cal["GANA"], cal["PIERDE"]) <= 0.05 * tot
                                      else "NO CUMPLE"), flush=True)


def main():
    print("decidir_p2_bloques de %s | calibración %d sorteos, semilla %d, tope %.2f por cola" % (
        X.__file__, X.N_CALIB_P2, X.SEMILLA_CALIB_P2, X.MAX_FALSOS_CALIB))
    escenario("B2 signo por noche, 6 noches x 6", [6] * 6, True)
    escenario("B4 iid en el borde, 2+2+1 pasadas", [2, 2, 1], False)
    escenario("B5 signo por noche, 3 noches x 2", [2] * 3, True)
    escenario("B6 signo por noche, 4 noches x 2", [2] * 4, True)
    escenario("B7 signo por noche, 5 noches x 2", [2] * 5, True)
    escenario("B8 signo por noche, 8 noches x 2", [2] * 8, True)
    escenario("B9 iid, 5 noches x 2", [2] * 5, False)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
