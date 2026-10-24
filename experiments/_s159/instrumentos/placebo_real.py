# -*- coding: utf-8 -*-
"""S159, tarea I2: el placebo de M sobre los pares REALES de K, antes de leer el A/B de D25.

POR QUÉ. La primera versión de este script (salida en placebo_real_salida_compuerta.txt) midió que, con el placebo
como compuerta, K×1,2 da MEJORA en VIIRS 750 z<=40 y en VIIRS 375 sin kernel z<=40, en V1 y en V2, porque K queda bajo
MIROVA: el A/B de D25 saldría INVALIDO pase lo que pase. Nicolás selló el 2026-10-21 el placebo como COMPARADOR
(ADENDA_PLACEBO.md, D-28, commit 2629f5a16). Este script es el control (i) y (iii) del §3 de esa adenda sobre los
datos de verdad: con D = K×1,2 y D = K×0,8 como brazo, d′ tiene que ser idénticamente 0 y ningún estrato que decide o
bloquea puede dar MEJORA; K×0,8 sigue dando EMPEORA por d. También informa lo que da el nulo (D = K) y el placebo SIN
comparador, que el evaluador sigue informando (§2.5).

Mismos pares que calibracion_previa.py (alertas de MIROVA que K publica con magnitud, por estrato). Sólo pares de K:
NO lee ninguna salida de los brazos del A/B (prohibido hasta el tag de lectura). Calibración: la simétrica (D-27), que
es sobre la que se escribió D-28; con la sellada el comparador no se aplica.

Uso: python placebo_real.py <TMP>      (necesita la copia unida de sustrato_k.py; la arma en <TMP>)
Termina con código 1 si algún control falla.
"""
import collections
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402


def main(tmp):
    datos, _ = S.unir_k(tmp)
    fallas = []
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
            nom, _ = X.estrato(clave, r.get("z"))
            pares[nom].append({"k": r["disp"], "d": r["disp"], "m": r["vrp_ref"], "clave": clave,
                               "bloque": "%s|%s" % (r["vol"], r["noche"])})
        ver0, info0 = X.evaluar_m(pares, ok_ctrl=True, modo_calib="simetrica")
        brazos = {g: X.evaluar_m({n: [dict(p, d=p["k"] * g) for p in P] for n, P in pares.items()},
                                 ok_ctrl=True, modo_calib="simetrica") for g in X.PLACEBO_GANANCIAS}
        print("\n== %s %s a %s | calibración simétrica (D-27) con el comparador de D-28" % (nombre, desde, hasta))
        for nom, modo in X.ESTRATOS:
            i = info0.get("M|%s" % nom, {})
            pl = info0["M_placebo"].get(nom, {})
            print("   %-26s %-8s n %3d noches %3d razón K %s | nulo %s | placebo sin comparador %s" % (
                nom, modo, i.get("n", 0), i.get("noches", 0),
                ("%.3f" % i["razon_K"]) if "razon_K" in i else "  -  ", ver0["M|%s" % nom],
                ", ".join("x%s %s" % (g, r) for g, r in pl.items()) or "-"))
            for g, (ver_g, info_g) in brazos.items():
                ig = info_g.get("M|%s" % nom, {})
                if "regla" not in ig:
                    continue
                dprima = ("regla sobre d′ %s, max |d′| %r, ĝ x%.4f" % (ig["regla_dprima"], ig["dprima_max_abs"],
                                                                        ig["g_hat_factor"])
                          if "regla_dprima" in ig else "sin comparador (estrato que informa)")
                print("      brazo D = K x %s: regla sobre d %-7s -> decide %-11s | %s%s" % (
                    g, ig["regla"], ver_g["M|%s" % nom], dprima, (" | nota: " + ig["nota"]) if ig.get("nota") else ""))
                if modo == "informa":
                    continue
                if ver_g["M|%s" % nom] == "MEJORA":
                    fallas.append("%s %s: K x %s da MEJORA con el comparador" % (nombre, nom, g))
                if ig.get("dprima_max_abs") != 0.0:
                    fallas.append("%s %s: K x %s con d′ distinto de 0 (%r)" % (nombre, nom, g, ig.get("dprima_max_abs")))
                if g == 0.8 and ig["regla"] == "EMPEORA" and ver_g["M|%s" % nom] != "EMPEORA":
                    fallas.append("%s %s: K x 0,8 da EMPEORA por d y el estrato no lo dice" % (nombre, nom))
            if modo != "informa" and "regla_dprima" in i:
                print("      nulo (D = K): ĝ x%.4f, max |d′| %r" % (i["g_hat_factor"], i["dprima_max_abs"]))
        empeora_08 = [nom for nom, modo in X.ESTRATOS if modo != "informa"
                      and brazos[0.8][0].get("M|%s" % nom) == "EMPEORA"]
        print("   K x 0,8 da EMPEORA por d en: %s" % (empeora_08 or "ningún estrato"))
        if not empeora_08:
            fallas.append("%s: K x 0,8 no da EMPEORA en ningún estrato que decide o bloquea" % nombre)
    print("\nRESUMEN: %s" % ("los controles (i) y (iii) de D-28 §3 pasan en V1 y V2" if not fallas
                             else "FALLAN: %s" % fallas))
    return 1 if fallas else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1]))
