# -*- coding: utf-8 -*-
"""Verificador del candado K (PR #858), parte 1: la regla exacta del evaluador sobre las clases REALES de la corrida C0.

1. pmf de ED.distribucion_x_exacta contra una convolucion propia con Fraction (math.comb), estrato por estrato reales.
2. x_obs, cola y p95 exacto de ED.g1 contra la cuenta propia, con la regla k encendida y apagada.
3. controles_del_nulo con la regla exacta: sin romper (tiene que dar OK) y con la pmf rota de cuatro maneras
   (tiene que dar FALLA). Si alguna rotura da OK, el control no ve esa rotura.
4. veredicto() en los cuatro casos de G1 con la regla W2 encendida y apagada.
Uso: python -I v1_regla_sobre_clases_reales.py <reeval_c0_resultado.json>
"""
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import evaluar_diurno as ED  # noqa: E402
from scipy import stats  # noqa: E402


def pmf_frac(estratos):
    pmf = [Fraction(1)]
    for n, p, k in estratos:
        tot = math.comb(n, p)
        f = [Fraction(math.comb(k, x) * math.comb(n - k, p - x), tot) for x in range(0, min(p, k) + 1)]
        out = [Fraction(0)] * (len(pmf) + len(f) - 1)
        for i, a in enumerate(pmf):
            for j, b in enumerate(f):
                out[i + j] += a * b
        pmf = out
    return pmf


def cargar(ruta):
    cl = json.load(open(ruta, encoding="utf-8"))["clases"]
    cls = {}
    for clave, c in cl.items():
        vol, sen, t = clave.split("|")
        cls[(vol, sen, t)] = {"ventana": c["ventana"], "pob": set(c["pob"]), "estado": c["estado"]}
    return cls


def main(ruta):
    cls = cargar(ruta)
    print("clases reales: %d | pasadas a la vez pos y neg: %d" % (
        len(cls), sum(1 for c in cls.values() if {"pos", "neg"} <= c["pob"])))
    for nom, ws in (("W2 a W6", ED.DECIDEN), ("W3 a W6", ED.SIN_W2)):
        est = ED.estratos_de(cls, ws)
        pf = pmf_frac(est)
        pe = ED.distribucion_x_exacta(est)
        L = max(len(pf), len(pe))
        dif = max(abs(float(pf[x] if x < len(pf) else 0) - float(pe[x] if x < len(pe) else 0)) for x in range(L))
        xobs_propio = sum(1 for k, c in cls.items() if c["ventana"] in ws and c["estado"] == "publicada" and "pos" in c["pob"])
        P = sum(e[1] for e in est); N = sum(e[0] - e[1] for e in est); K = sum(e[2] for e in est)
        cola_f = sum(pf[xobs_propio:])
        cdf = 0; q = None
        for x, v in enumerate(pf):
            cdf += v
            if cdf >= Fraction(95, 100):
                q = x
                break
        print("\n== %s: %d estratos, P %d N %d K %d | len pmf ED %d, Fraction %d | max |pmf ED - Fraction| %.3e"
              % (nom, len(est), P, N, K, len(pe), len(pf), dif))
        for regla in (False, True):
            ED.REGLA.update(cola_exacta=regla, w2_decide_nicolas=regla)
            r = ED.g1(cls, ws, np.random.default_rng(ED.SEMILLA))
            print("   regla %-14s x_obs ED %d propio %d | cola ED %.10f Fraction %.10f (dif %.1e) | p95 exacto ED %+.6f propio %+.6f | veredicto %s"
                  % ("cola exacta" if regla else "p95 muestreado", r["x_obs"], xobs_propio, r["p_cola_exacta"], float(cola_f),
                     abs(r["p_cola_exacta"] - float(cola_f)), r["p95_exacto"], q / P - (K - q) / N, r["veredicto"]))
        # cola de la regla «>» para mostrar que el codigo usa «>=»
        print("   P(X > x_obs) Fraction %.6f (lo que daria la mutacion «>»)" % float(sum(pf[xobs_propio + 1:])))
        # controles del nulo con la regla exacta
        ED.REGLA.update(cola_exacta=True, w2_decide_nicolas=True)
        orig = ED.distribucion_x_exacta
        roturas = {
            "sin romper": None,
            "pmf corrida +1 (cola de x-1)": lambda e: np.concatenate([[0.0], orig(e)])[:len(orig(e))] if True else None,
            "pmf corrida -1": lambda e: np.concatenate([orig(e)[1:], [0.0]]),
            "sin estratos (una sola hipergeometrica)": lambda e: stats.hypergeom(sum(s[0] for s in e), sum(s[2] for s in e), sum(s[1] for s in e)).pmf(np.arange(sum(s[1] for s in e) + 1)),
            "binomial por estrato (con reposicion)": lambda e: _binom(e),
        }
        for etq, f in roturas.items():
            ED.distribucion_x_exacta = f if f else orig
            try:
                c = ED.controles_del_nulo(cls, ws, np.random.default_rng(0))
            finally:
                ED.distribucion_x_exacta = orig
            print("   control del nulo, %-40s -> %s | %s" % (etq, "OK" if c["ok"] else "FALLA", c["texto"]))
    # veredicto con la regla W2
    print("\n== veredicto() en los cuatro casos de G1")
    base = {"repetir": [], "ventanas_presentes": list(ED.DECIDEN), "G3": "CUMPLE",
            "G2": {s: {"veredicto": "FALLA"} for s in ED.VIIRS}}
    for regla in (False, True):
        ED.REGLA.update(w2_decide_nicolas=regla)
        for a in ("CUMPLE", "FALLA"):
            for b in ("CUMPLE", "FALLA"):
                for g2 in ("CUMPLE", "FALLA"):
                    res = dict(base, G1_W2W6={"veredicto": a}, G1_W3W6={"veredicto": b},
                               G2={s: {"veredicto": g2} for s in ED.VIIRS})
                    print("   regla W2 %-5s G1 con W2 %-6s sin W2 %-6s G2 %-6s -> %s" % (regla, a, b, g2, ED.veredicto(res, [])[:60]))
        res = dict(base, G1_W2W6={"veredicto": "SIN SUSTRATO"}, G1_W3W6={"veredicto": "CUMPLE"})
        print("   regla W2 %-5s G1 con W2 SIN SUSTRATO sin W2 CUMPLE -> %s" % (regla, ED.veredicto(res, [])[:60]))


def _binom(e):
    pmf = np.array([1.0])
    for n, p, k in e:
        pmf = np.convolve(pmf, stats.binom(p, k / n if n else 0).pmf(np.arange(p + 1)))
    return pmf


if __name__ == "__main__":
    main(sys.argv[1])
