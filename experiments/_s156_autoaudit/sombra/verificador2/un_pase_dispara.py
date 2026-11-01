"""Hallazgo 3: con la funcion real, una sola Muy Bajo V375 diferencial dispara INVESTIGAR. Uso: python un_pase_dispara.py <copia>"""
import sys
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[1] + "/scripts")
import scripts.vigilancia_sombra as vs


def p(f, prod, som):
    return {"volcano": "Isluga", "sensor": "VIIRS375", "fecha_utc": f, "vrp_mirova_mw": 0.2, "protegida": False,
            "referencia_sospechosa": False, "prod_pub": prod, "sombra_pub": som}


d = vs.disparadores([p("2026-10-20 05:00", False, True)], [], hoy="2026-10-20", adopcion="2026-10-18 09:57")
print("una sola Muy Bajo perdida:", d["veredicto"], d["muy_bajo"])
d = vs.disparadores([p("2026-10-20 05:00", False, True)] + [p("2026-10-2%d 05:00" % i, True, True) for i in (1, 3, 5, 7)],
                    [], hoy="2026-10-28", adopcion="2026-10-18 09:57")
print("1 de 5:", d["veredicto"], d["muy_bajo"])
d = vs.disparadores([p("2026-10-2%d 05:00" % i, True, True) for i in (1, 3, 5, 7)], [], hoy="2026-10-28",
                    adopcion="2026-10-18 09:57")
print("control 0 de 4:", d["veredicto"], d["muy_bajo"])
