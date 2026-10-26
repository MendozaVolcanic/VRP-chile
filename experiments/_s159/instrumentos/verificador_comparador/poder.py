# -*- coding: utf-8 -*-
"""Verificador S159: poder del comparador D-28 con los tamaños reales de V1 y V2 (pares de K, pares_k.json).
Brazo: cada par se lleva una fracción alfa del camino hacia MIROVA en log (efecto real, "sube los pares que debe
subir") con ruido lognormal por par de desviación sigma (log10). Para cada (alfa, sigma) se repite con N semillas y se
cuenta cuántas veces el estrato da MEJORA final (con comparador) y MEJORA por d sola (sin comparador, lo que daba D-27).
Sólo los dos estratos que pueden dar MEJORA (VIIRS750 z<=40 y VIIRS375 sin kernel z<=40; los de z>40 no pueden: uno
tiene un solo volcán con 3 pares, el otro sólo bloquea). Proxy de CUMPLE: MEJORA en algún estrato de V1 Y de V2 con la
misma semilla (las demás pruebas P1, P2 dadas por buenas).
Control positivo: sigma = 0 (determinista) tiene que dar MEJORA; control negativo: alfa = 0 con ganancia 1,3 y ruido
(familia E de experimentos.py) no puede dar MEJORA (medido allí: 0 de 96).
"""
import json, sys, collections
from multiprocessing import Pool
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / "_s157_prereg_d25"))
N = 12
ESTR = ("VIIRS750|z<=40", "VIIRS375|sin_kernel|z<=40")


def una(a):
    import evaluar_d25 as X
    w, nom, alfa, sig, s, P = a
    K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P]); lK = np.log10(K / M)
    rng = np.random.default_rng(1000 * s + int(sig * 1000) + int(alfa * 100))
    D = M * 10 ** ((1 - alfa) * lK + rng.normal(0, sig, len(P)))
    r, det = X.decidir_estrato([dict(p, d=float(x)) for p, x in zip(P, D)], "decide", "simetrica", True)
    return (w, nom, alfa, sig, s, r, det["regla"], det.get("regla_dprima"), det.get("calibrada_dprima"))


def main():
    D = json.loads((AQUI / "pares_k.json").read_text(encoding="utf-8"))
    t = [(w, nom, alfa, sig, s, D[w][nom]) for w in ("V1", "V2") for nom in ESTR for alfa in (0.25, 0.5)
         for sig in (0.0, 0.03, 0.05, 0.075, 0.10, 0.15) for s in range(N if sig > 0 else 1)]
    with Pool(8) as pool:
        R = pool.map(una, t, chunksize=1)
    json.dump(R, open(AQUI / "poder_salida.json", "w", encoding="utf-8"))
    g = collections.defaultdict(list)
    for x in R:
        g[(x[0], x[1], x[2], x[3])].append(x)
    print("ventana estrato alfa sigma | n | MEJORA final | MEJORA por d | d' MEJORA | d' calibración falla")
    for k in sorted(g):
        v = g[k]
        print("%s %-26s %.2f %.3f | %2d | %2d | %2d | %2d | %d" % (k + (len(v), sum(x[5] == "MEJORA" for x in v),
              sum(x[6] == "MEJORA" for x in v), sum(x[7] == "MEJORA" for x in v), sum(x[8] is False for x in v))))
    print("\nproxy CUMPLE (MEJORA en algún estrato de V1 y de V2, misma semilla) | con comparador | sólo d")
    for alfa in (0.25, 0.5):
        for sig in (0.0, 0.03, 0.05, 0.075, 0.10, 0.15):
            ss = range(N if sig > 0 else 1)
            def ok(w, s, col):
                return any(x[col] == "MEJORA" for x in R if x[0] == w and x[2] == alfa and x[3] == sig and x[4] == s)
            c = sum(ok("V1", s, 5) and ok("V2", s, 5) for s in ss)
            d = sum(ok("V1", s, 6) and ok("V2", s, 6) for s in ss)
            print("alfa %.2f sigma %.3f | %d de %d | %d de %d" % (alfa, sig, c, len(ss), d, len(ss)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
