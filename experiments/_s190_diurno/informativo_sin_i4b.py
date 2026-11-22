# -*- coding: utf-8 -*-
"""INFORMATIVO, NO DECIDE. Lo que daría el evaluador sellado si se dejara pasar UN caso de la compuerta I4 (b).

Por qué existe. Con la regla sellada (adenda V sobre S163 §5), el A/B sale INVÁLIDO POR INSTRUMENTO por un solo caso:
«I4b Isluga|MODIS|2026-07-22: pasadas diurnas de MIROVA y ningún record diurno del brazo». La causa no es un brazo roto
ni NASA: el único gránulo diurno de Terra de ese día sobre Isluga (MOD021KM.A2026203.1225) se bajó y se procesó, y la
vía lo descartó por borde (171-01, `scripts/run_pipeline.py`), el mismo descarte que de noche entra en la vara de I4 (c).
Dejar pasar ese caso es una desviación de la regla sellada y sólo la puede decidir Nicolás. Este script calcula, para
que la vea, qué veredicto saldría si la aceptara. Nada de aquí entra al veredicto que decide.

Uso: igual que evaluar_diurno_via.py, con --ignorar-i4b <volcán|sensor|día> (repetible).
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import evaluar_diurno_via as ev  # noqa: E402


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ignorar = []
    while "--ignorar-i4b" in argv:
        i = argv.index("--ignorar-i4b")
        ignorar.append(argv[i + 1])
        del argv[i:i + 2]
    if not ignorar:
        print("falta --ignorar-i4b")
        return 2
    original = ev.compuerta_i4

    def compuerta_i4_menos(*a, **k):
        prob, det = original(*a, **k)
        quitar = {"I4b %s: pasadas diurnas de MIROVA y ningún record diurno del brazo" % x for x in ignorar}
        return [p for p in prob if p not in quitar], det

    ev.compuerta_i4 = compuerta_i4_menos
    print("INFORMATIVO, NO DECIDE: se deja pasar I4b en %s (desviación que sólo decide Nicolás)" % ignorar)
    return ev.main(argv)


if __name__ == "__main__":
    sys.exit(main())
