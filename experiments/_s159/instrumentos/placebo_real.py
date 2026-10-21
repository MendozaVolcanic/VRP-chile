# -*- coding: utf-8 -*-
"""S159, tarea I2: el placebo obligatorio de M sobre los pares REALES de K, antes de que corra el A/B de D25.

POR QUÉ. La prueba unitaria muestra que el placebo invalida cuando K queda bajo MIROVA; falta saber qué pasa con los
datos de verdad: si el placebo invalida en las ventanas V1 y V2 del pre-registro, el A/B de D25 saldrá INVALIDO POR
INSTRUMENTO pase lo que pase con D25, y eso es una decisión de Nicolás (el sello D-27 y el placebo chocan).
Mismos pares que calibracion_previa.py (alertas de MIROVA que K publica con magnitud, por estrato), con D = K (nulo):
lo único que se mide es qué hace la métrica con K×1,2 y K×0,8. Se corre con las dos calibraciones.

Uso: python placebo_real.py <TMP>      (necesita la copia unida de sustrato_k.py; la arma en <TMP>)
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
        for calib in ("simetrica", "sellada"):
            ver, info = X.evaluar_m(pares, ok_ctrl=True, modo_calib=calib)
            print("\n== %s %s a %s | calibración %s | PLACEBO: %s" % (nombre, desde, hasta, calib, ver["PLACEBO"]))
            for nom, modo in X.ESTRATOS:
                i = info.get("M|%s" % nom, {})
                pl = info["M_placebo"].get(nom, {})
                print("   %-26s %-8s n %3d noches %3d razón K %s -> nulo %s | placebo %s" % (
                    nom, modo, i.get("n", 0), i.get("noches", 0),
                    ("%.3f" % i["razon_K"]) if "razon_K" in i else "  -  ", ver["M|%s" % nom],
                    ", ".join("x%s %s" % (g, r) for g, r in pl.items()) or "-"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
