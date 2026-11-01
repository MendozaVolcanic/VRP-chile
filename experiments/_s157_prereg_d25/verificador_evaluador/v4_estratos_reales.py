# -*- coding: utf-8 -*-
"""Verificador del evaluador de D25 (S157). Sobre los MISMOS pares reales de K que usa calibracion_previa.py (copia
unida en D:\\vrp-trabajo\\temporales\\s157d25, efecto del probe del L1B: x1,09 en VIIRS 375 y x1,14 en VIIRS 750):

  1. composición de cada estrato: pares, bloques noche-volcán, volcanes y la fracción del volcán más grande
     (la dependencia ENTRE noches de un mismo volcán no la absorben los bloques noche-volcán).
  2. calibración con TRES nulos, 200 repeticiones, signo por bloque noche-volcán, la misma regla_m del evaluador:
       a) el sellado (signo de log D/K), como evaluar_d25.calibrar
       b) simétrico: signo de d (mediana verdadera 0 por construcción), las dos colas por separado
       c) simétrico con bloques = volcán para el signo (dependencia entre noches de un volcán)
Uso: python v4_estratos_reales.py > v4_salida.txt
"""
import collections
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(r"D:\vrp-trabajo\s157-prereg-d25")
sys.path.insert(0, str(REPO / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402

E_SENSOR = {"VIIRS375": math.log10(1.09), "VIIRS750": math.log10(1.14)}


def tasa_simetrica(d, W, bl, semilla=99, n=200):
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    r = np.random.default_rng(semilla); c = collections.Counter()
    for _ in range(n):
        s = r.choice((-1.0, 1.0), size=len(uniq))[idx]
        c[X.regla_m(s * d, W)[0]] += 1
    return c["MEJORA"] / n, c["EMPEORA"] / n


def main():
    datos, _ = S.unir_k(r"D:\vrp-trabajo\temporales\verif_eval\v4")
    for nombre, (desde, hasta, ref, solo_tabla) in S.VENTANAS.items():
        filas = S.fk.cargar_filas(ref, solo_tabla)
        recs, _ = S.fk.etiquetar_todo(datos, filas, (desde, hasta), set(S.bp.VOLS))
        pares = collections.defaultdict(list)
        for r in recs:
            if r["b"] not in X.SENS or r["lab"] != "pos" or not r["pub"] or not r.get("vrp_ref") or not (r.get("disp") or 0) > 0:
                continue
            if solo_tabla and r["noche"] < "2026-04-01":
                continue
            clave = "%s|%s|%s" % (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))
            nom, modo = X.estrato(clave, r.get("z"))
            pares[nom].append({"k": r["disp"], "m": r["vrp_ref"], "d": r["disp"] * 10 ** E_SENSOR[r["b"]],
                               "bloque": "%s|%s" % (r["vol"], r["noche"]), "vol": r["vol"]})
        print("\n== %s %s a %s" % (nombre, desde, hasta), flush=True)
        for nom, modo in X.ESTRATOS:
            P = pares.get(nom, [])
            if len(P) < X.N_MIN_PARES:
                print("   %-26s n %d: SIN SUSTRATO" % (nom, len(P))); continue
            bl = [p["bloque"] for p in P]; vols = collections.Counter(p["vol"] for p in P)
            top = vols.most_common(1)[0]
            W = X.pesos_bloque(bl)
            fm, fe, _ = X.calibrar(P, W, bloques=bl)
            K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P]); D = np.array([p["d"] for p in P])
            d = np.abs(np.log10(D / M)) - np.abs(np.log10(K / M))
            sm, se = tasa_simetrica(d, W, bl)
            vm, ve = tasa_simetrica(d, W, [p["vol"] for p in P])
            print("   %-26s %-8s n %3d bloques %3d volcanes %2d (mayor %s %d = %.0f %%) | sellado MEJORA %.3f EMPEORA %.3f | simétrico MEJORA %.3f EMPEORA %.3f | simétrico signo por volcán MEJORA %.3f EMPEORA %.3f"
                  % (nom, modo, len(P), len(set(bl)), len(vols), top[0], top[1], 100 * top[1] / len(P), fm, fe, sm, se, vm, ve), flush=True)


if __name__ == "__main__":
    main()
