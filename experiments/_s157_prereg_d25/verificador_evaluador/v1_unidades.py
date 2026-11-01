# -*- coding: utf-8 -*-
"""Verificador del evaluador de D25 (S157). Pruebas de unidad SIN tocar evaluar_d25.py: lo importa y llama a sus
funciones puras. Correr con PYTHONDONTWRITEBYTECODE=1.

  V1a mediana ponderada contra np.median(np.repeat(...)) en casos al azar con empates
  V1b pesos_bloque: los pares de un bloque heredan el mismo conteo; la suma de conteos por réplica = n bloques
  V1c percentil del intervalo: regla_m usa 2,5 y 97,5 sobre las medianas de las réplicas
  V1d global_ventana: P2 PIERDE con un estrato de M INDECIDIBLE (calibración): ¿qué devuelve?
  V1e combinar: V1 MEJORA y V2 "NO CUMPLE (M empeora)"; y V1 empeora+mejora (DECIDE) con V2 MEJORA
  V1f peor(): "MEJORA" contra "SIN EFECTO"
  V1g binomial: probabilidad de declarar mal calibrada una regla PERFECTA con 200 repeticiones y tope 5 %
  V1h calibrar con efecto NULO verdadero (d simétrico, K lejos de MIROVA) y con K ya sobre MIROVA
  V1i control positivo: tope min(e, a) contra "signo fijo hacia MIROVA" literal
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(r"D:\vrp-trabajo\s157-prereg-d25")
sys.path.insert(0, str(REPO / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)


# ---------------- V1a
rng = np.random.default_rng(1)
malos = 0
for it in range(300):
    n = int(rng.integers(1, 25))
    d = np.round(rng.normal(0, 1, n), 1)          # redondeo: fuerza empates
    W = rng.integers(0, 4, size=(20, n))
    W[:, 0] += 1                                  # al menos un par por réplica
    got = X.medianas_ponderadas(d, W)
    ref = np.array([np.median(np.repeat(d, w)) for w in W])
    malos += int(not np.allclose(got, ref))
p("V1a mediana ponderada: %d de 300 casos distintos de np.median(np.repeat)" % malos)

# ---------------- V1b
bl = ["a", "a", "b", "c", "c", "c"]
W = X.pesos_bloque(bl, n_boot=2000, semilla=3)
igual_en_bloque = all((W[:, 0] == W[:, 1]).all() and (W[:, 3] == W[:, 4]).all() and (W[:, 4] == W[:, 5]).all() for _ in [0])
suma_bloques = np.unique(W[:, [0, 2, 3]].sum(axis=1))
p("V1b pesos_bloque: pares del mismo bloque con igual conteo %s | suma de conteos de bloques por réplica %s (n bloques 3)"
  % (igual_en_bloque, suma_bloques))
# media de cada conteo de bloque ~ 1
p("    media del conteo por bloque", np.round(W[:, [0, 2, 3]].mean(axis=0), 3))

# ---------------- V1c
d = np.array([-0.3, -0.2, -0.1, -0.05, 0.02, -0.4, -0.25])
Wd = X.pesos_bloque(list(range(len(d))))
meds = X.medianas_ponderadas(d, Wd)
r, lo, hi = X.regla_m(d, Wd)
p("V1c regla_m: %s [%.4f, %.4f] | np.percentile 2,5/97,5 de las medianas [%.4f, %.4f]" % (
    r, lo, hi, np.percentile(meds, 2.5), np.percentile(meds, 97.5)))

# ---------------- V1d
ver = {"P1|VIIRS375": "CUMPLE", "P1|VIIRS750": "CUMPLE", "P2|VIIRS375": "PIERDE", "P2|VIIRS750": "EMPATE",
       "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
for nom, modo in X.ESTRATOS:
    ver["M|%s" % nom] = "NEUTRO"
ver["M|VIIRS750|z<=40"] = "INDECIDIBLE"          # p. ej. calibración "ambos" (calibracion_previa_salida.txt)
p("V1d global_ventana(P2 PIERDE, un estrato de M INDECIDIBLE):", X.global_ventana(ver, True))
ver["M|VIIRS750|z<=40"] = "NEUTRO"
p("    global_ventana(P2 PIERDE, M todo NEUTRO):", X.global_ventana(ver, True))

# ---------------- V1e
tmp = Path(r"D:\vrp-trabajo\temporales\verif_eval\v1")
tmp.mkdir(parents=True, exist_ok=True)
casos = {
    "v1_mejora": {"ventana": "V1", "estado": "MEJORA", "mejora": True, "empeora": False},
    "v2_empeora": {"ventana": "V2", "estado": "NO CUMPLE (M empeora)", "mejora": False, "empeora": True},
    "v1_mixto": {"ventana": "V1", "estado": "DECIDE NICOLAS (M mejora en un estrato y empeora en otro)", "mejora": True, "empeora": True},
    "v2_mejora": {"ventana": "V2", "estado": "MEJORA", "mejora": True, "empeora": False},
    "v2_sin": {"ventana": "V2", "estado": "SIN EFECTO", "mejora": False, "empeora": False},
    "v1_p1b": {"ventana": "V1", "estado": "SIN EFECTO | P1b: protegidas que cruzan 1 MW hacia abajo, decide Nicolas", "mejora": False, "empeora": False},
}
for n, d_ in casos.items():
    json.dump(d_, open(tmp / (n + ".json"), "w", encoding="utf-8"))
for a, b in (("v1_mejora", "v2_empeora"), ("v1_mixto", "v2_mejora"), ("v1_mejora", "v2_sin"), ("v1_p1b", "v2_sin")):
    p("V1e combinar(%s, %s) ->" % (a, b), X.combinar([tmp / (a + ".json"), tmp / (b + ".json")]))

# ---------------- V1f
p("V1f peor(['MEJORA', 'SIN EFECTO']) =", X.peor(["MEJORA", "SIN EFECTO"]),
  "| peor(['SIN EFECTO', 'DECIDE NICOLAS (x)']) =", X.peor(["SIN EFECTO", "DECIDE NICOLAS (x)"]))

# ---------------- V1g
from math import comb


def cola(n, pp, k):  # P(X > k)
    return sum(comb(n, i) * pp ** i * (1 - pp) ** (n - i) for i in range(k + 1, n + 1))


tope = int(X.MAX_FALSOS_CALIB * X.N_CALIB)
for pp in (0.05, 0.04, 0.025):
    p("V1g regla con tasa real de falsos %.3f: P(más de %d de %d) = %.3f" % (pp, tope, X.N_CALIB, cola(X.N_CALIB, pp, tope)))

# ---------------- V1h
def sintetico(razon_k, n_bloques=40, por_bloque=3, e_med=0.05, semilla=11):
    r = np.random.default_rng(semilla)
    P, bl = [], []
    for b in range(n_bloques):
        for _ in range(por_bloque):
            m = 10 ** r.normal(0, 0.5)
            k = m * razon_k * 10 ** r.normal(0, 0.15)
            e = abs(r.normal(0, e_med))
            P.append({"k": k, "m": m, "d": k * 10 ** e}); bl.append(b)
    return P, bl


for razon in (0.5, 1.0):
    P, bl = sintetico(razon)
    W = X.pesos_bloque(bl)
    fm, fe, poder = X.calibrar(P, W, bloques=bl)
    # nulo alternativo: la DIFERENCIA d con signo al azar por bloque (mediana verdadera 0 por construcción)
    K = np.array([q["k"] for q in P]); M = np.array([q["m"] for q in P]); D = np.array([q["d"] for q in P])
    d = np.abs(np.log10(D / M)) - np.abs(np.log10(K / M))
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    r2 = np.random.default_rng(5); c = {"MEJORA": 0, "EMPEORA": 0, "NEUTRO": 0}
    for _ in range(200):
        s = r2.choice((-1.0, 1.0), size=len(uniq))[idx]
        c[X.regla_m(s * d, W)[0]] += 1
    p("V1h razón K/MIROVA %.1f: nulo sellado (signo de log D/K) MEJORA %.3f EMPEORA %.3f | nulo simétrico (signo de d) MEJORA %.3f EMPEORA %.3f"
      % (razon, fm, fe, c["MEJORA"] / 200, c["EMPEORA"] / 200))

# ---------------- V1i
# Un par con K a factor 1,5 bajo MIROVA y D25 que sube x3 (se pasa): literal "hacia MIROVA" = K*3 -> d > 0
k, m, dd = 1.0, 1.5, 3.0
e = abs(math.log10(dd / k)); a = abs(math.log10(k / m))
lit = abs(math.log10(k * 10 ** e / m)) - a
top = abs(math.log10(k * 10 ** min(e, a) / m)) - a
p("V1i control positivo, par K=1 M=1,5 D=3: d literal (signo hacia MIROVA, |e| entero) %+.3f | d con tope min(e,a) %+.3f" % (lit, top))
