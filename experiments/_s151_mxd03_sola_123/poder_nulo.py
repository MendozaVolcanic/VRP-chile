# Tarea 1.23: poder del rango de M contra los K nulos en la regla 1, dicho antes de correr.
#
# POR QUE. M es determinista (mismo L1B, mismo codigo): repetira las 2 perdidas y las 9 ganadas de la
# 1.21 salvo deriva. Lo unico incierto es la distribucion del nulo. Con K nulos el p de Monte Carlo mas
# chico es 1/(K+1); con K = 20 es 0,048, el primer K que baja de 0,05. Aca se calcula, para nulos
# binomiales homogeneos (cada protegida que C publica se pierde con probabilidad qL; cada una que C no
# publica se gana con qG), la probabilidad de que el rango declare las perdidas o las ganadas de M como
# especificas de MxD03. La 1.21 dio un solo sorteo del nulo en km: 4 de 9 perdidas (qL ~ 0,44) y 5 de 37
# ganadas (qG ~ 0,135). Es un modelo para el poder, no una medida: la medida es la corrida.
#
# Uso: python poder_nulo.py [--salida x.txt]
import argparse
import io
import math
import sys
from pathlib import Path

C_PUBLICA, C_NO_PUBLICA = 9, 37        # protegidas de la muestra: 46, C publica 9 (1.21, verificado)
L_M, G_M = 2, 9                        # lo que M dio en la 1.17 y en la 1.21


def cola_alta(n, q, x):
    """P(Bin(n, q) >= x)."""
    return sum(math.comb(n, i) * q ** i * (1 - q) ** (n - i) for i in range(x, n + 1))


def p_especifico(n, q, obs, k):
    """P(p de Monte Carlo de la cola alta <= 0,05) con k nulos: cuantos nulos pueden llegar a obs o mas."""
    pmax = max(m for m in range(k + 1) if (1 + m) / (k + 1) <= 0.05) if (1 / (k + 1)) <= 0.05 else -1
    if pmax < 0:
        return 0.0
    t = cola_alta(n, q, obs)                     # prob. de que UN nulo llegue a obs o mas
    return sum(math.comb(k, m) * t ** m * (1 - t) ** (k - m) for m in range(pmax + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    buf = io.StringIO()
    p = lambda *x: print(*x, file=buf)  # noqa: E731
    p("p de Monte Carlo minimo: K=19 %.4f, K=20 %.4f, K=40 %.4f" % (1 / 20, 1 / 21, 1 / 41))
    p("\nPerdidas: M pierde %d de las %d protegidas que C publica" % (L_M, C_PUBLICA))
    for q in (0.05, 0.10, 0.22, 0.44):
        p("  qL %.2f: P(un nulo pierde >= %d) %.3f | P(PERDIDAS ESPECIFICAS) K=20 %.3f, K=40 %.3f" % (
            q, L_M, cola_alta(C_PUBLICA, q, L_M), p_especifico(C_PUBLICA, q, L_M, 20), p_especifico(C_PUBLICA, q, L_M, 40)))
    p("\nGanancias: M gana %d de las %d protegidas que C no publica" % (G_M, C_NO_PUBLICA))
    for q in (0.05, 0.08, 0.10, 0.135, 0.20):
        p("  qG %.3f: P(un nulo gana >= %d) %.3f | P(GANANCIAS ESPECIFICAS) K=20 %.3f, K=40 %.3f" % (
            q, G_M, cola_alta(C_NO_PUBLICA, q, G_M), p_especifico(C_NO_PUBLICA, q, G_M, 20),
            p_especifico(C_NO_PUBLICA, q, G_M, 40)))
    sys.stdout.write(buf.getvalue())
    if a.salida:
        Path(a.salida).write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main()
