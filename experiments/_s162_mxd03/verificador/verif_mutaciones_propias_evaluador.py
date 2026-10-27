# -*- coding: utf-8 -*-
"""Verificador S162 MxD03, afirmacion A4: mutaciones PROPIAS del evaluador (distintas de las 5 del auditor), contra las
12 pruebas de probar_evaluar_mxd03.py y contra la prueba de punta a punta. Mide la cobertura real de la suite sobre el
camino que corre main(): una mutacion que ninguna prueba atrapa es un hueco.
Se cuenta ATRAPADA solo si falla una asercion (no una excepcion), como manda S156.

Mutaciones:
  V1 vara_desde_estado devuelve siempre "NO DETIENE"   (la funcion que main() usa de verdad; regla_vara, la probada, no)
  V2 veredicto con vara None da CUMPLE SIN DAÑO          (en vez de PENDIENTE DE LA VARA)
  V3 control_r_modulo devuelve siempre OK                (control 2 del §8 muerto)
  V4 control_cableado devuelve siempre OK                (control 8 muerto)
  V5 control_geometria devuelve siempre OK               (control 1 muerto; lo cubre punta a punta?)
  V6 p1b devuelve siempre []                              (cruce de 1 MW mudo)
  V7 _invisible devuelve siempre False                    (partidas entran a P2; debe atraparla la 6)
  V8 r_vivo devuelve siempre True                         (control 2 inerte; debe atraparla la 3)
  V9 ruido_p2 devuelve el MAYOR de 20 (percentil 100)     (en vez del segundo mayor)
  V10 saldo cuenta solo negativos (ignora bajo1 sin publicar)
  V11 veredicto: INDECIDIBLE de un control externo (geometria, union, procedencia) ignorado
Uso: cd experiments/_s162_mxd03 && PYTHONIOENCODING=utf-8 python verificador/verif_mutaciones_propias_evaluador.py
"""
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
AB = AQUI.parent
sys.path.insert(0, str(AB))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import evaluar_mxd03 as E  # noqa: E402
import probar_evaluar_mxd03 as PE  # noqa: E402


def mutaciones():
    real_ver = E.veredicto

    def v2(res):
        if res.get("vara") is None:
            res = dict(res, vara="NO DETIENE")
        return real_ver(res)

    def v11(res):
        ctl = {k: v for k, v in res["controles"].items() if k in ("cobertura", "k2", "arnes", "r_modulo")}
        return real_ver(dict(res, controles=ctl))

    real_saldo = E.saldo

    def v10(fs, b):
        return sum(1 for f in fs if f["lab"] == "neg_limpio" and f["pub"].get(b, f["pub"]["K"]) == 1)

    return (
        ("V1 vara_desde_estado siempre NO DETIENE", patch.object(E, "vara_desde_estado", lambda s: "NO DETIENE")),
        ("V2 vara None -> CUMPLE", patch.object(E, "veredicto", v2)),
        ("V3 control_r_modulo siempre OK", patch.object(E, "control_r_modulo", lambda f: {"estado": "OK", "malos": [], "n_malos": 0})),
        ("V4 control_cableado siempre OK", patch.object(E, "control_cableado", lambda f: {"estado": "OK", "malos": [], "n_malos": 0})),
        ("V5 control_geometria siempre OK", patch.object(E, "control_geometria", lambda f: {"estado": "OK"})),
        ("V6 p1b siempre []", patch.object(E, "p1b", lambda f: [])),
        ("V7 _invisible siempre False", patch.object(E, "_invisible", lambda f: False)),
        ("V8 r_vivo siempre True", patch.object(E, "r_vivo", lambda f: True)),
        ("V9 ruido = maximo de 20", patch.object(E, "ruido_p2", lambda dr: max((abs(x) for x in dr), default=0))),
        ("V10 saldo sin bajo1", patch.object(E, "saldo", v10)),
        ("V11 veredicto ignora controles externos", patch.object(E, "veredicto", v11)),
    )


def punta_a_punta_pasa():
    """Corre probar_punta_a_punta.py en subproceso: no ve los parches de este proceso, asi que aqui solo sirve como
    referencia de que la prueba pasa sin mutar. Las mutaciones V1 a V11 se evaluan contra las 12 pruebas en proceso."""
    p = subprocess.run([sys.executable, str(AB / "probar_punta_a_punta.py")], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(AB))
    return p.returncode == 0


def main():
    base = PE.pruebas(E)
    print("sin mutar: %d de %d pasan" % (sum(ok for _, ok, _ in base), len(base)))
    resumen = []
    for nombre, parche in mutaciones():
        with parche:
            r = PE.pruebas(E)
        caidas = [n for n, ok, d in r if not ok and str(d).startswith("EXCEPCION")]
        fallan = [n for n, ok, d in r if not ok and not str(d).startswith("EXCEPCION")]
        estado = "ATRAPADA por " + "; ".join(x[:2] for x in fallan) if fallan else "NO ATRAPADA"
        if caidas:
            estado += " (caidas: %d)" % len(caidas)
        resumen.append((nombre, bool(fallan)))
        print("%-45s %s" % (nombre, estado))
    print("punta a punta sin mutar pasa:", punta_a_punta_pasa())
    n = sum(a for _, a in resumen)
    print("mutaciones propias atrapadas por las 12 pruebas: %d de %d" % (n, len(resumen)))
    print("NO atrapadas:", [m for m, a in resumen if not a])


if __name__ == "__main__":
    main()
