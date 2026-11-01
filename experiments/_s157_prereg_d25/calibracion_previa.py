# -*- coding: utf-8 -*-
"""S157, tarea 1.29, candado. ¿La calibración de M del pre-registro (§5) deja decidir con los datos reales?

POR QUÉ. La regla sellada dice que M de un estrato queda INDECIDIBLE si, con efectos del tamaño observado y signo al
azar, la regla da MEJORA o EMPEORA en más del 5 % de 200 repeticiones. Pero un cambio de signo al azar ALEJA a la
magnitud de MIROVA cuando ya está cerca (si |log10(K/MIROVA)| < e, d > 0 con cualquier signo), así que en un estrato
donde K ya calza con MIROVA el nulo da EMPEORA aunque D25 no haga nada sistemático. Este script mide, ANTES de correr el
A/B, en cuántos estratos pasaría eso, con los pares reales de K en disco (los mismos del sustrato) y el tamaño de efecto
que midió el probe del L1B de Chillán: e = log10(1,09) en VIIRS 375 y log10(1,14) en VIIRS 750. Separa los falsos
MEJORA de los falsos EMPEORA.

Uso: python calibracion_previa.py > calibracion_previa_salida.txt   (necesita la copia unida de sustrato_k.py)
"""
import collections
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402

E_SENSOR = {"VIIRS375": math.log10(1.09), "VIIRS750": math.log10(1.14)}   # probe_l1b/README.md, Resultado


def main():
    datos, _ = S.unir_k(r"D:\vrp-trabajo\temporales\s157d25")
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
                               "bloque": "%s|%s" % (r["vol"], r["noche"])})
        print("\n== %s %s a %s" % (nombre, desde, hasta))
        for nom, modo in X.ESTRATOS:
            P = pares.get(nom, [])
            if len(P) < X.N_MIN_PARES:
                print("   %-26s %-8s n %3d: SIN SUSTRATO" % (nom, modo, len(P)))
                continue
            W = X.pesos_bloque([p["bloque"] for p in P])
            K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P]); e = np.log10(np.array([p["d"] for p in P]) / K)
            # la misma función del evaluador (signo sorteado por noche-volcán)
            f_mej, f_emp, _ = X.calibrar(P, W, [p["bloque"] for p in P])
            cuenta = {"MEJORA": round(f_mej * X.N_CALIB), "EMPEORA": round(f_emp * X.N_CALIB)}
            cuenta["NEUTRO"] = X.N_CALIB - cuenta["MEJORA"] - cuenta["EMPEORA"]
            cerca = float(np.mean(np.abs(np.log10(K / M)) < e))
            falsos = f_mej + f_emp
            d = np.abs(np.log10(K * 10 ** e / M)) - np.abs(np.log10(K / M))
            s_mej, s_emp, s_pod = X.calibrar_simetrico(d, W, [p["bloque"] for p in P])
            vols = collections.Counter(p["bloque"].split("|")[0] for p in P)
            print("   %-26s simétrica: MEJORA %.3f EMPEORA %.3f poder %s | volcanes %s" % (nom, s_mej, s_emp, s_pod, dict(vols.most_common())))
            print("   %-26s %-8s n %3d | razón K mediana %.3f | pares con |log K/M| < e: %.1f %% | nulo: MEJORA %3d, EMPEORA %3d, NEUTRO %3d de %d -> sellada (ambos): %s | sólo MEJORA: %s" % (
                nom, modo, len(P), float(np.median(K / M)), 100 * cerca, cuenta["MEJORA"], cuenta["EMPEORA"], cuenta["NEUTRO"],
                X.N_CALIB, "calibrada" if falsos <= X.MAX_FALSOS_CALIB else "MAL CALIBRADA (INDECIDIBLE)",
                "calibrada" if f_mej <= X.MAX_FALSOS_CALIB else "MAL CALIBRADA (INDECIDIBLE)"))


if __name__ == "__main__":
    main()
