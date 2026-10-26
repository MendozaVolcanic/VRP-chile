# -*- coding: utf-8 -*-
"""S159, D-32: la calibración de d′ con 1.000 repeticiones sobre los mismos pares que usó el verificador.

POR QUÉ. El verificador con contexto limpio (verificador_comparador/INFORME.md, H2; script nulo_dprima.py) midió que con
la semilla de d′ (SEMILLA + 3) y 200 repeticiones, V2 VIIRS 750 z<=40 da 11 falsos MEJORA de 200 contra un tope de 10:
la cola binomial fijada por una semilla. Nicolás decidió (D-32) subir a 1.000 repeticiones y sellar semilla y número
antes del tag. Este script mide qué da con 1.000, contra el tope de 50 (el mismo 5 % por cola).

Mismos pares y mismo D que el verificador: los pares REALES de K de verificador_comparador/pares_k.json (armados con
armar_pares.py, la selección de placebo_real.py; ningún brazo del A/B) y el D sintético de nulo_dprima.py: a mitad de
camino hacia MIROVA en log10, determinista y con ruido 0,05 (generador 205). Control del instrumento: con 200
repeticiones tiene que reproducir lo que midió el verificador (0,050 y 0,055 en V2 VIIRS 750 z<=40).

Uso: python calib_dprima_1000.py
"""
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

PARES = AQUI / "verificador_comparador" / "pares_k.json"


def main():
    D = json.loads(PARES.read_text(encoding="utf-8"))
    print("semilla de d′ %d (SEMILLA + 3), repeticiones del evaluador %d, tope %.0f %% por cola" % (
        X.SEMILLA_CALIB_DPRIMA, X.N_CALIB_DPRIMA, 100 * X.MAX_FALSOS_CALIB))
    for w, nom in (("V2", "VIIRS750|z<=40"), ("V1", "VIIRS750|z<=40"), ("V2", "VIIRS375|sin_kernel|z<=40"),
                   ("V1", "VIIRS375|sin_kernel|z<=40")):
        P = D[w][nom]
        K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P]); lK = np.log10(K / M)
        bl = [p["bloque"] for p in P]; W = X.pesos_bloque(bl)
        for et, lD in (("mitad de camino, determinista", 0.5 * lK),
                       ("mitad de camino, ruido 0,05 (gen. 205)",
                        0.5 * lK + np.random.default_rng(200 + 5).normal(0, 0.05, len(P)))):
            gh = np.median(lD - lK)
            dp = np.round(np.abs(lD) - np.abs(lK + gh), X.DEC_DPRIMA)
            linea = []
            for n in (200, 1000):
                fm, fe, _ = X.calibrar_simetrico(dp, W, bl, n_rep=n, semilla=X.SEMILLA_CALIB_DPRIMA)
                tope = X.MAX_FALSOS_CALIB * n
                linea.append("%d rep: falsos MEJORA %d (tope %d) %s, EMPEORA %d" % (
                    n, round(fm * n), tope, "OK" if fm <= X.MAX_FALSOS_CALIB else "FALLA", round(fe * n)))
            print("%s %-26s n %3d | %-40s | %s" % (w, nom, len(P), et, " | ".join(linea)), flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
