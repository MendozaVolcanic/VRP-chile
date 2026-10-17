# Tarea 1.21: cobertura del intervalo de Delta medida con respuesta conocida (A110: el control se valida
# midiendo su nulo, no razonandolo).
#
# POR QUE. El balance de la regla 2 expande cada celda (volcan x estrato de la 1.17) desde 3 a 30
# granulos medidos hasta cientos de negativos limpios. Que el intervalo cubra lo que dice no se puede
# argumentar: se mide. Este script toma escenarios donde el valor de CADA granulo de la poblacion es
# conocido, repite muchas veces el muestreo con el mismo n por celda que tiene la muestra real, y cuenta
# en que fraccion el intervalo contiene el total verdadero. Escenarios:
#   replay : el cambio de publicacion CC menos C que da el replay sobre los records guardados
#            (prediccion_cumulo.json): el efecto grande que se espera de la etiqueta del cumulo;
#   nulo   : nada cambia;
#   raro   : 2 % de 0->1 y 2 % de 1->0 al azar en toda la poblacion;
#   A_solo : 0->1 en 30 % de los negativos limpios del estrato A y nada en el resto (efecto localizado);
#   mezcla : el replay, mas 5 % de 1->0 al azar;
#   apaga_50 / apaga_70 / apaga_90: el brazo apaga ese porcentaje de las publicaciones que C hace en
#            negativos limpios (verdad NEGATIVA: la unica via a MEJORA; verificador del pre-registro);
#   enciende_5 / enciende_10: enciende ese porcentaje de los negativos limpios que C no publica.
# "decide el signo" es, con verdad negativa, la probabilidad de MEJORA; con positiva, la de EMPEORA.
# Uso: python cobertura_estimador.py [--reps 400]   (escribe cobertura_estimador_salida.txt)
import argparse
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import evaluar_cumulo as E  # noqa: E402

POB = AQUI.parent / "_s151_mxd03_etiquetas" / "poblacion.json"


def celdas_poblacion(pob, pred):
    """{celda: (valores de la poblacion para el escenario replay, n medido en la muestra real)}."""
    n_muestra = {}
    for vol, v in pob["volcanes"].items():
        for g in v["muestra"]:
            if g["lab"] == "neg_limpio":
                n_muestra[(vol, g["estrato"])] = n_muestra.get((vol, g["estrato"]), 0) + 1
    out = {}
    for vol, filas in pred["poblacion"].items():
        for clave, estrato, lab, prot, pub_c, pub_cc in filas:
            if lab != "neg_limpio" or estrato == "sin":   # como en evaluar_cumulo
                continue
            out.setdefault((vol, estrato), {"replay": [], "pub_c": [], "n": n_muestra.get((vol, estrato), 0)})
            out[(vol, estrato)]["replay"].append(pub_cc - pub_c)
            out[(vol, estrato)]["pub_c"].append(pub_c)
    return out


def escenarios(celdas, rng):
    out = {}
    for k, c in celdas.items():
        N = len(c["replay"])
        rep = np.array(c["replay"])
        u = rng.random(N)
        raro = np.where(u < 0.02, 1, np.where(u > 0.98, -1, 0))
        a_solo = (rng.random(N) < 0.30).astype(int) if k[1] == "A" else np.zeros(N, dtype=int)
        mezcla = np.where(rng.random(N) < 0.05, -1, rep)
        pc = np.array(c["pub_c"])
        out[k] = {"replay": rep, "nulo": np.zeros(N, dtype=int), "raro": raro, "A_solo": a_solo, "mezcla": mezcla}
        for f in (50, 70, 90):
            out[k]["apaga_%d" % f] = np.where((pc == 1) & (rng.random(N) < f / 100.0), -1, 0)
        for f in (5, 10):
            out[k]["enciende_%d" % f] = np.where((pc == 0) & (rng.random(N) < f / 100.0), 1, 0)
    return out


def dirichlet_rechazado(cel, rng, draws=4000, prior=0.5):
    """La primera version del estimador (posterior de Dirichlet de Jeffreys por celda). Se conserva para
    que su falla se pueda reproducir: con 2 a 6 granulos en 32 de las 37 celdas que se expanden el medio conteo arrastra la media de
    cada celda hacia 1/3 y el sesgo se suma en el mismo sentido en todas ellas."""
    tot = np.zeros(draws)
    for vals, N in cel.values():
        n, s = len(vals), sum(vals)
        if n >= N:
            tot += s
            continue
        c = np.array([vals.count(-1), vals.count(0), vals.count(1)], dtype=float)
        th = rng.dirichlet(c + prior, size=draws)
        resto = rng.multinomial(N - n, th)
        tot += s + resto[:, 2] - resto[:, 0]
    return [float(x) for x in np.percentile(tot, [2.5, 97.5])]


def metodos():
    return {"principal (evaluar_cumulo.balance)": lambda cel, rng: E.balance(cel, 0)["intervalo"],
            "wilson_por_celda (1.17)": lambda cel, rng: E.balance(cel, 0)["intervalo_wilson_por_celda"],
            "dirichlet_1/2 (rechazado)": dirichlet_rechazado}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    a = ap.parse_args()
    pob = json.load(open(POB, encoding="utf-8"))
    pred = json.load(open(AQUI / "prediccion_cumulo.json", encoding="utf-8"))
    rng = np.random.default_rng(20261016)
    celdas = celdas_poblacion(pob, pred)
    esc = escenarios(celdas, rng)
    lineas = []
    for nombre in ("replay", "nulo", "raro", "A_solo", "mezcla", "apaga_50", "apaga_70", "apaga_90",
                   "enciende_5", "enciende_10"):
        verdad = int(sum(e[nombre].sum() for e in esc.values()))
        for mnombre, m in metodos().items():
            dentro, anchos, signo_ok = 0, [], 0
            for _ in range(a.reps):
                cel = {}
                for k, c in celdas.items():
                    vals = esc[k][nombre]
                    n = min(c["n"], len(vals))
                    idx = rng.choice(len(vals), size=n, replace=False)
                    cel["%s/%s" % k] = ([int(x) for x in vals[idx]], len(vals))
                lo, hi = m(cel, np.random.default_rng(int(rng.integers(1 << 30))))
                dentro += lo <= verdad <= hi
                anchos.append(hi - lo)
                signo_ok += (lo > 0) if verdad > 0 else ((hi < 0) if verdad < 0 else (lo <= 0 <= hi))
            lineas.append("%-11s verdad %6d | %-36s cobertura %.3f | ancho mediano %7.1f | decide el signo %.3f" % (
                nombre, verdad, mnombre, dentro / a.reps, float(np.median(anchos)), signo_ok / a.reps))
            print(lineas[-1], flush=True)
    (AQUI / "cobertura_estimador_salida.txt").write_text("reps %d\n" % a.reps + "\n".join(lineas) + "\n",
                                                          encoding="utf-8")


if __name__ == "__main__":
    main()
