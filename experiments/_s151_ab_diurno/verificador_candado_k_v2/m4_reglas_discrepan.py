# -*- coding: utf-8 -*-
"""¿Hay casos plausibles en que la regla de la adenda (cola exacta) y la vieja (p95 muestreado) dan veredicto distinto
sobre los MISMOS datos? Si los hay y el arnés no tiene ninguno, una mutación que intercambie las reglas (g1_regla_inversa)
pasa en verde. Busca sobre cls sintéticos (estratos chicos y medianos, semilla del evaluador) y sobre el caso de empate
del arnés. No toca archivos."""
import contextlib, io, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import probar_evaluar_diurno as PE
ED = PE.ED
np = ED.np

def ambas(cls):
    out = {}
    for nom, cola in (("cola exacta", True), ("p95 muestreado", False)):
        ED.REGLA.update(cola_exacta=cola, w2_decide_nicolas=False)
        r = ED.g1(cls, ("W3",), np.random.default_rng(ED.SEMILLA))
        out[nom] = r
    return out

rnd = random.Random(5)
hall, prob = [], 0
for _ in range(400):
    est = []
    for _s in range(rnd.randint(2, 5)):
        n = rnd.randint(20, 120); p = rnd.randint(2, 10); k = rnd.randint(3, n // 3)
        est.append((n, p, k))
    P = sum(e[1] for e in est)
    pmf = ED.distribucion_x_exacta(est)
    colas = pmf[::-1].cumsum()[::-1]
    # x observado justo en el borde: el menor x con cola < 0,05 y el anterior
    crit = [x for x in range(len(pmf)) if colas[x] < 0.05]
    if not crit:
        continue
    for x in (crit[0] - 1, crit[0]):
        if x < 0:
            continue
        xs, resto = [], x
        for (n, p, k) in est:
            t = min(resto, p, k); xs.append(t); resto -= t
        if resto:
            continue
        prob += 1
        r = ambas(PE._cls_desde_estratos(est, xs))
        a, b = r["cola exacta"], r["p95 muestreado"]
        if a["veredicto"] != b["veredicto"]:
            hall.append((est, x, a["veredicto"], a["p_cola_exacta"], b["veredicto"], b["D"], b["p95"], a["p95_exacto"]))
print("casos probados en el borde del soporte crítico:", prob, "| con veredicto distinto:", len(hall))
for h in hall[:8]:
    print("  estratos %s x=%d | cola exacta %s (P=%.4f) | p95 muestreado %s (D %+.4f, p95 %+.4f, p95 exacto %+.4f)" % h)
cls_e = PE._cls_desde_estratos([(4, 2, 2), (6, 1, 2)], [2, 1])
r = ambas(cls_e)
print("empate del arnés [(4,2,2),(6,1,2)] x=3: cola exacta %s | p95 muestreado %s  -> %s" % (
    r["cola exacta"]["veredicto"], r["p95 muestreado"]["veredicto"],
    "las dos reglas dan lo mismo: el caso no distingue la regla" if r["cola exacta"]["veredicto"] == r["p95 muestreado"]["veredicto"] else "distingue"))
