# -*- coding: utf-8 -*-
"""Verificador S159, pregunta 4: el nulo de la calibración de d′ (D-28 §2.3 y §3) sobre los pares reales de K.
(a) Centrado: con el sorteo de signo por bloque (calibrar_simetrico), la media de las medianas por réplica y la
fracción de réplicas MEJORA/EMPEORA, con 20 semillas en lugar de la única fija (SEMILLA + 3), para ver cuánto del
"calibrada sí/no" depende de la semilla en el estrato donde falla (V2 VIIRS750 z<=40).
(b) Tasa binomial de referencia: si la regla fuera perfecta (2,5 % por cola), ¿con qué probabilidad pasa 10 de 200?
Brazo usado: alfa = 0,5 hacia MIROVA con ruido 0,05 (el de experimentos.py, C2 semilla 5), y el determinista.
Instrumento: 1) si el sorteo no estuviera centrado, la media de medianas se alejaría de 0 más que su error; 2) control
positivo: con todos los signos hacia MIROVA (-|d′|) la regla da MEJORA (poder True).
"""
import json, sys
from math import comb
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
D = json.loads((AQUI / "pares_k.json").read_text(encoding="utf-8"))
p_bin = sum(comb(200, k) * 0.025 ** k * 0.975 ** (200 - k) for k in range(11, 201))
print("(b) P(>= 11 de 200 | 2,5 %% por cola) = %.4f" % p_bin)
for w, nom in (("V2", "VIIRS750|z<=40"), ("V1", "VIIRS750|z<=40"), ("V2", "VIIRS375|sin_kernel|z<=40")):
    P = D[w][nom]
    K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P]); lK = np.log10(K / M)
    for et, lD in (("alfa0.5 determinista", 0.5 * lK),
                   ("alfa0.5 sigma0.05 s5", 0.5 * lK + np.random.default_rng(200 + 5).normal(0, 0.05, len(P)))):
        g = lD - lK; gh = np.median(g)
        dp = np.round(np.abs(lD) - np.abs(lK + gh), X.DEC_DPRIMA)
        bl = [p["bloque"] for p in P]; W = X.pesos_bloque(bl)
        uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
        a = np.abs(dp)
        rng = np.random.default_rng(99)
        meds = [np.median(X.medianas_ponderadas(rng.choice((-1.0, 1.0), size=len(uniq))[idx] * a, W)) for _ in range(200)]
        fm, fe = [], []
        for k in range(20):
            m_, e_, poder = X.calibrar_simetrico(dp, W, bl, semilla=X.SEMILLA + 3 + k)
            fm.append(m_); fe.append(e_)
        fallan = sum(1 for m_, e_ in zip(fm, fe) if m_ > 0.05 or e_ > 0.05)
        print("%s %-26s %-22s n %d bloques %d | media de medianas nulas %+.5f (sd %.5f, error %.5f) | semilla sellada fM %.3f fE %.3f | 20 semillas: fM media %.4f max %.3f, fE media %.4f max %.3f, calibración falla en %d de 20 | poder %s" % (
            w, nom, et, len(P), len(uniq), np.mean(meds), np.std(meds), np.std(meds) / np.sqrt(200), fm[0], fe[0],
            np.mean(fm), max(fm), np.mean(fe), max(fe), fallan, poder))
