# -*- coding: utf-8 -*-
"""S204: exceso mínimo detectable por volcán para el NO CUMPLE de la zona A (s 3, piso 0,0025) contra NHI.
POR QUÉ: el pre-registro S194 §4.5 (que el S196 usa sin cambios, §6) manda que un NO CUMPLE se anote en
docs/BEYOND_MIROVA_EXTENSIONS.md §12 (MEJ-5) «con los números y el exceso mínimo detectable de cada volcán», porque NO
CUMPLE con poco poder no es «no hay señal». `evaluar.py poder` sólo da una tabla genérica (n_S 10, 20, 40 contra
n_N 80); aquí se usa la misma función sellada (`minimo_detectable`, hipergeométrica exacta de una cola, sin estratos de
nubosidad) con los n_S, n_N y la tasa basal de N que dio la corrida real (resultado_nhi_s203.json).
Es una aproximación de la prueba que votó (que permuta dentro de estratos de nubosidad), así que el mínimo es orden de
magnitud, no frontera exacta. No re-evalúa nada ni cambia el veredicto.
Uso: python exceso_minimo_s204.py <resultado_nhi_s203.json>"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_s194_lab_zona_a"))
import evaluar as E  # noqa: E402  (la vara S194 sellada)


def main(argv):
    res = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    print("veredicto de la corrida: %s" % res["veredicto"])
    print("exceso mínimo detectable (p < %.2f, una cola, hipergeométrica sin estratos; E.minimo_detectable)" % E.ALFA)
    print("%-17s %4s %4s %6s %9s %9s %10s %10s %9s  %s" % (
        "volcan", "n_S", "n_N", "basal", "alert_S", "tasa_S", "min_alert", "min_tasa", "min_exc", "voto"))
    for vol, d in res["nhi"].items():
        n_s, n_n = d["n_S"], d["n_N"]
        p0 = d["alertas_N"] / n_n if n_n else 0.0
        k = E.minimo_detectable(n_s, n_n, p0) if n_s and n_n else None
        tasa_s = d["alertas_S"] / n_s if n_s else float("nan")
        print("%-17s %4d %4d %6.3f %9d %9.3f %10s %10s %9s  %s" % (
            vol, n_s, n_n, p0, d["alertas_S"], tasa_s,
            "-" if k is None else k,
            "-" if k is None else "%.3f" % (k / n_s),
            "-" if k is None else "%.3f" % (k / n_s - p0),
            d["voto"]))
    print("(min_alert '-' = ni con todas las noches S en alerta se llega a p < %.2f)" % E.ALFA)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
