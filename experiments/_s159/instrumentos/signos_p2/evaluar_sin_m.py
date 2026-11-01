# -*- coding: utf-8 -*-
"""S161: copia sin cambios de experiments/_s159/instrumentos/placebos_d44/evaluar_sin_m.py, para los placebos de D-45
(placebo_signos.py). Texto original:
Corre experiments/_s157_prereg_d25/evaluar_d25.py tal cual, con UNA sola diferencia: la métrica de magnitud M no se
calcula (evaluar_m devuelve SIN SUSTRATO en todos los estratos, la misma rama que el evaluador usa cuando un estrato no
tiene pares). Sólo para los placebos de P2 de D-44.

POR QUÉ. Los placebos miden P2, y P2 se decide en contar ANTES de M y sin leer nada de M (contribuciones_p2 y
decidir_p2_bloques sólo leen la tabla K-brazo y la protección). M, con sus calibraciones de d y d′ (200 y 1.000
repeticiones por estrato y por regla, más el placebo de M), es la mayor parte del tiempo de cada corrida, y aquí hay
cientos. Control de que no cambia P2: comparar_sin_m.py corre la misma semilla con el evaluador entero y con éste y
exige que el detalle de P2 sea idéntico en las dos reglas y los dos sensores.

Uso: los mismos argumentos que evaluar_d25.py.
"""
import sys
from pathlib import Path

EVD = Path(__file__).resolve().parents[4] / "experiments" / "_s157_prereg_d25"
sys.path.insert(0, str(EVD))
import evaluar_d25 as X  # noqa: E402


def evaluar_m_sin_calculo(pares, ok_ctrl, modo_calib=X.CALIB_MODO):
    ver, info = {}, {}
    todos = [p for P in pares.values() for p in P]
    info["M_pares_con_magnitud_distinta"] = sum(abs(p["d"] - p["k"]) > 1e-9 for p in todos)
    info["M_pares"] = len(todos)
    info["M_placebo"] = {}
    for nom, modo in X.ESTRATOS:
        P = pares.get(nom, [])
        ver["M|%s" % nom] = "SIN SUSTRATO"
        info["M|%s" % nom] = {"n": len(P), "noches": len({p["bloque"] for p in P}), "modo": modo,
                              "nota": "M no calculada (evaluar_sin_m.py, placebos de P2 de D-44)"}
    return ver, info


X.evaluar_m = evaluar_m_sin_calculo

if __name__ == "__main__":
    sys.exit(X.main())
