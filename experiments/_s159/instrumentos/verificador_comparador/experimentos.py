# -*- coding: utf-8 -*-
"""Verificador S159 del comparador D-28 (evaluar_d25.py en b4258040c). Corre la decisión de M de cada estrato que
decide o bloquea (X.decidir_estrato, la función de producción del evaluador, sin copiar) sobre brazos SINTÉTICOS
construidos desde los pares REALES de K (pares_k.json, armado por armar_pares.py). Ningún dato de los brazos del A/B.

Las dos preguntas del instrumento:
 1. ¿Si el comparador estuviera roto, esto lo vería? Sí para "ganancia uniforme da MEJORA" (familia A: si d′ no se
    aplicara, el control positivo PLACEBO_SIN_COMP muestra MEJORA y la fila con comparador también la mostraría).
 2. ¿Si el instrumento estuviera muerto, se vería distinto? Cada fila imprime además la regla sobre d sin comparador
    (r_d) y el estado del comparador por separado; un brazo que no se mueve (D = K) da r_d NEUTRO, y el control
    positivo (mitad de camino con ruido 0) tiene que dar r_d MEJORA. Una fila con r_d NEUTRO no cuenta como "el
    comparador bloqueó": la que cuenta es r_d MEJORA y final != MEJORA.

Familias (log en base 10, l = log10(x/MIROVA)):
  A  ganancia uniforme g (incluye g* = la que centra la mediana de K en MIROVA)        -> nunca debe dar MEJORA
  B1 ganancia por volcán que centra cada volcán en MIROVA (límite declarado §3)         -> se informa
  B2 ganancia por volcán al azar en [1,2; 3,0], uniforme dentro del volcán               -> límite declarado
  C1 mitad de camino (contracción alfa) determinista                                     -> efecto real
  C2 contracción alfa=0,5 con ruido lognormal por par                                    -> efecto real con ruido
  C3 sólo los pares más lejos (l < mediana) a mitad de camino; el resto igual            -> efecto real dirigido
  C4 sube sólo los pares bajo MIROVA, contracción 0,5; los que están sobre, igual        -> efecto real que sólo sube
  C5 ganancia uniforme g0 + contracción alfa (mezcla: sube a todos y además corrige)     -> efecto real mixto
  D  ganancia que depende sólo de la magnitud de K (débiles suben más), sin MIROVA        -> placebo no uniforme
  E  ganancia uniforme ĝ con ruido lognormal por par (sin información de MIROVA)         -> nulo con ruido
Ventanas: V1 y V2, con sus tamaños reales. Salida: experimentos_salida.json + texto por stdout.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))

SEMILLAS = range(8)


def brazos(P, nom):
    K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P])
    lK = np.log10(K / M); lk = np.log10(K)
    vols = [p["clave"].split("|")[0] for p in P]
    out = []
    gstar = 10 ** (-np.median(lK))
    for g in (0.5, 0.8, 1.2, 1.5, 2.0, 3.0, gstar):
        out.append(("A", "g=%.3f" % g, K * g))
    gv = {v: 10 ** (-np.median(lK[[x == v for x in vols]])) for v in set(vols)}
    out.append(("B1", "g_v centra cada volcan", K * np.array([gv[v] for v in vols])))
    for s in SEMILLAS:
        rng = np.random.default_rng(100 + s)
        gr = {v: rng.uniform(1.2, 3.0) for v in sorted(set(vols))}
        out.append(("B2", "seed%d" % s, K * np.array([gr[v] for v in vols])))
    for a in (0.25, 0.5, 0.75):
        out.append(("C1", "alfa=%.2f" % a, M * 10 ** ((1 - a) * lK)))
    for sig in (0.05, 0.1, 0.2):
        for s in SEMILLAS:
            rng = np.random.default_rng(200 + s)
            out.append(("C2", "alfa=0.5 sigma=%.2f seed%d" % (sig, s), M * 10 ** (0.5 * lK + rng.normal(0, sig, len(P)))))
    lejos = lK < np.median(lK)
    out.append(("C3", "solo lejos a mitad", np.where(lejos, M * 10 ** (0.5 * lK), K)))
    out.append(("C4", "solo bajo MIROVA a mitad", np.where(lK < 0, M * 10 ** (0.5 * lK), K)))
    for g0, a in ((1.2, 0.25), (1.5, 0.25), (1.2, 0.5)):
        out.append(("C5", "g0=%.1f + alfa=%.2f" % (g0, a), M * 10 ** ((1 - a) * lK + np.log10(g0))))
    for b in (0.2, 0.4):
        out.append(("D", "beta=%.1f" % b, K * 10 ** (-b * (lk - np.median(lk)))))
    for sig in (0.1, 0.2):
        for s in SEMILLAS:
            rng = np.random.default_rng(300 + s)
            out.append(("E", "g=1.3 sigma=%.2f seed%d" % (sig, s), K * 1.3 * 10 ** rng.normal(0, sig, len(P))))
    return out


def una(args):
    import evaluar_d25 as X
    w, nom, modo, P, fam, et, Dv = args
    Q = [dict(p, d=float(x)) for p, x in zip(P, Dv)]
    r, det = X.decidir_estrato(Q, modo, "simetrica", True)
    return {"w": w, "nom": nom, "modo": modo, "fam": fam, "et": et, "final": r, "r_d": det["regla"],
            "calib_d": det["calibrada"], "vols_d": det["volcanes_con_d_negativa"],
            "r_dp": det.get("regla_dprima"), "calib_dp": det.get("calibrada_dprima"),
            "fm_dp": det.get("falsos_mejora_dprima"), "fe_dp": det.get("falsos_empeora_dprima"),
            "vols_dp": det.get("volcanes_con_dprima_negativa"), "g_hat": det.get("g_hat_factor"),
            "dp_med": det.get("dprima_mediana"), "ic_dp": det.get("ic95_dprima"), "d_med": det["d_mediana"],
            "nota": det["nota"]}


def main():
    import evaluar_d25 as X
    D = json.loads((AQUI / "pares_k.json").read_text(encoding="utf-8"))
    tareas = []
    for w, est in D.items():
        for nom, modo in X.ESTRATOS:
            if modo == "informa" or nom not in est:
                continue
            P = est[nom]
            for fam, et, Dv in brazos(P, nom):
                if modo == "bloquea" and fam not in ("A", "C1"):
                    continue
                tareas.append((w, nom, modo, P, fam, et, Dv))
    print("tareas", len(tareas), flush=True)
    with Pool(10) as pool:
        res = pool.map(una, tareas, chunksize=1)
    (AQUI / "experimentos_salida.json").write_text(json.dumps(res, indent=0), encoding="utf-8")
    for x in res:
        print("%s %-26s %-3s %-30s final %-8s | d %-7s cal %s v%d | d' %-7s cal %s (fM %.3f fE %.3f) v%s | ghat %.3f d'med %+.4f IC [%+.4f,%+.4f]" % (
            x["w"], x["nom"], x["fam"], x["et"], x["final"], x["r_d"], "ok" if x["calib_d"] else "MAL", x["vols_d"],
            x["r_dp"], "ok" if x["calib_dp"] else "MAL", x["fm_dp"] or 0, x["fe_dp"] or 0, x["vols_dp"],
            x["g_hat"] or 0, x["dp_med"] or 0, *(x["ic_dp"] or [0, 0])))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
