# -*- coding: utf-8 -*-
"""Verificador D-42, afirmacion 6 por otro camino: tasa de falsos GANA y PIERDE de P2 CALIBRADA (funcion real
decidir_p2_bloques del evaluador de hoy) en los escenarios A, B7 y B8 de cobertura_p2_calibrada.py, con
  (a) OTRAS semillas (100000..100000+n-1), mismo generador, y
  (b) el espejo exacto de la muestra del implementador (semillas 0..499): cada conjunto c y su reflejo -c.
      Bajo el nulo simetrico, P(GANA) = P(PIERDE) exactamente; si el codigo es simetrico, el veredicto de -c es el de c
      con GANA y PIERDE intercambiados, y la tasa por cola libre de la asimetria de la muestra es (GANA + PIERDE)/2.

Pregunta 1 (¿veria una regla rota?): la columna «sin calibrar» reproduce la regla de D-34 y el espejo detecta cualquier
asimetria del codigo entre las colas (un veredicto de -c que no sea el intercambio del de c).
Pregunta 2 (¿veria un instrumento muerto?): el escenario C (efecto grande, 100 conjuntos) tiene que dar GANA casi
siempre; y cada conjunto produce un veredicto (la suma de categorias es n).

Datos 100 % sinteticos. Uso: python v02_falsos_otro_camino.py <n nuevas semillas> <n espejos> [escenarios]
"""
import collections
import math
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

N_NUEVAS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
N_ESPEJO = int(sys.argv[2]) if len(sys.argv) > 2 else 500
SOLO = sys.argv[3].split(",") if len(sys.argv) > 3 else None
ESPEJO = {"GANA": "PIERDE", "PIERDE": "GANA", "INDECIDIBLE": "INDECIDIBLE", "SIN SUSTRATO": "SIN SUSTRATO"}


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


def contrib(signos_por_noche, vol="Lascar"):
    out = []
    for n, cs in enumerate(signos_por_noche):
        for j, c in enumerate(cs):
            out.append({"clave": "%s|VIIRS375|2026-09-%02d 05:%02d" % (vol, n + 1, j), "c": int(c),
                        "bloque": "%s|2026-09-%02d" % (vol, n + 1)})
    return out


GEN = {
    "A": ("A nulo iid (12 noches x 3 pasadas, p=0.5)", lambda r: [r.choice((-1, 1), size=3) for _ in range(12)]),
    "B7": ("B7 nulo signo comun por noche (5 noches x 2)", lambda r: [[r.choice((-1, 1))] * 2 for _ in range(5)]),
    "B8": ("B8 nulo signo comun por noche (8 noches x 2)", lambda r: [[r.choice((-1, 1))] * 2 for _ in range(8)]),
    "C": ("C efecto grande a favor de D (p(-1)=0.85, 12 x 3) CONTROL POSITIVO",
          lambda r: [r.choice((-1, 1), size=3, p=(0.85, 0.15)) for _ in range(12)]),
}


def nuevas(nombre, gen, n, base=100000):
    t0 = time.time()
    cal, sin = collections.Counter(), collections.Counter()
    for i in range(n):
        v, det = X.decidir_p2_bloques(contrib(gen(np.random.default_rng(base + i))), ok_ctrl=True)
        cal[v] += 1
        sin[det["resultado_sin_calibrar"]] += 1
    assert sum(cal.values()) == n
    print("%-58s semillas %d..%d n=%d" % (nombre, base, base + n - 1, n))
    print("   CALIBRADA    GANA %s | PIERDE %s | (GANA+PIERDE)/2 %.4f | INDECIDIBLE %s | BLOQUEA %s | EMPATE %s" % (
        fmt(cal["GANA"], n), fmt(cal["PIERDE"], n), (cal["GANA"] + cal["PIERDE"]) / (2 * n), fmt(cal["INDECIDIBLE"], n),
        fmt(cal["BLOQUEA"], n), fmt(cal["EMPATE"], n)))
    print("   SIN CALIBRAR GANA %s | PIERDE %s | (GANA+PIERDE)/2 %.4f | %.0fs" % (
        fmt(sin["GANA"], n), fmt(sin["PIERDE"], n), (sin["GANA"] + sin["PIERDE"]) / (2 * n), time.time() - t0), flush=True)


def espejo(nombre, gen, n):
    """Semillas 0..n-1 del implementador: c y -c. Cuenta las parejas cuyo veredicto calibrado no es el intercambio."""
    t0 = time.time()
    cal, calm, rotas = collections.Counter(), collections.Counter(), []
    for s in range(n):
        pn = gen(np.random.default_rng(s))
        c = contrib(pn)
        cm = [dict(x, c=-x["c"]) for x in c]
        v, det = X.decidir_p2_bloques(c, ok_ctrl=True)
        vm, detm = X.decidir_p2_bloques(cm, ok_ctrl=True)
        cal[v] += 1
        calm[vm] += 1
        esperado = ESPEJO.get(v)
        if esperado is not None and vm != esperado:
            rotas.append((s, v, vm))
        if v in ("GANA", "PIERDE", "INDECIDIBLE") and (det["falsos_gana"], det["falsos_pierde"]) != (detm["falsos_pierde"], detm["falsos_gana"]):
            rotas.append((s, "falsos no espejados", det["falsos_gana"], det["falsos_pierde"], detm["falsos_gana"], detm["falsos_pierde"]))
    print("%-58s ESPEJO semillas 0..%d" % (nombre, n - 1))
    print("   original c : GANA %s | PIERDE %s | INDECIDIBLE %s | BLOQUEA %s | EMPATE %s" % (
        fmt(cal["GANA"], n), fmt(cal["PIERDE"], n), fmt(cal["INDECIDIBLE"], n), fmt(cal["BLOQUEA"], n), fmt(cal["EMPATE"], n)))
    print("   reflejo -c : GANA %s | PIERDE %s | INDECIDIBLE %s | BLOQUEA %s | EMPATE %s" % (
        fmt(calm["GANA"], n), fmt(calm["PIERDE"], n), fmt(calm["INDECIDIBLE"], n), fmt(calm["BLOQUEA"], n), fmt(calm["EMPATE"], n)))
    print("   tasa por cola libre de la asimetria de la muestra (GANA_c + GANA_-c)/(2n) = %.4f | parejas no espejadas %d %s | %.0fs" % (
        (cal["GANA"] + calm["GANA"]) / (2 * n), len(rotas), rotas[:5], time.time() - t0), flush=True)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("decidir_p2_bloques de %s | N_BOOT %d SEMILLA %d | calibracion %d sorteos, semilla %d, tope %.2f" % (
        X.__file__, X.N_BOOT, X.SEMILLA, X.N_CALIB_P2, X.SEMILLA_CALIB_P2, X.MAX_FALSOS_CALIB), flush=True)
    for k in (SOLO or ("C", "B7", "B8", "A")):
        nombre, gen = GEN[k]
        if k == "C":
            nuevas(nombre, gen, min(100, N_NUEVAS))
            continue
        if N_ESPEJO and k in ("A", "B7"):
            espejo(nombre, gen, N_ESPEJO)
        nuevas(nombre, gen, N_NUEVAS)


if __name__ == "__main__":
    main()
