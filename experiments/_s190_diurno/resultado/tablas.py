# -*- coding: utf-8 -*-
"""Tablas del informe del veredicto, impresas desde los JSON del evaluador (ningún número se copia a mano, S91).
Uso: python -I tablas.py <veredicto.json> <informativo_sin_i4b.json>"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def mw(x):
    try:
        return float(x.rsplit("|", 1)[1].split()[0])
    except (ValueError, IndexError):
        return None


for ruta, titulo in zip(sys.argv[1:3], ["Regla sellada (decide)", "INFORMATIVO: dejando pasar el I4b de Isluga (no decide)"]):
    d = json.load(open(ruta, encoding="utf-8"))
    p = d["principal"]
    print("### %s\n" % titulo)
    print("Compuertas que fallan: %s\n" % (p["compuertas"]["invalido"] + p["compuertas"]["indecidible"] or "ninguna"))
    print("Veredicto final por opción: %s\n" % {k: v[0] for k, v in d["final"].items()})
    print("| sensor | protegidas recuperadas | alertas recuperadas | negativos publicados | base (caso) | sin Chillán | sin W7 | M5 pares, mediana | M8 ≥1 MW sin fila | veredicto del sensor |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for s, m in p["por_sensor"].items():
        print("| %s | %d de %d | %d de %d | %d de %d | %s (%s) | %s | %s | %d, %.3f | %d | %s |" % (
            s, m["P"], m["P_obs"], m["alertas_recuperadas"], m["alertas_obs"], m["neg_pub"], m["neg_obs"], m["base"],
            m["caso"], m["sin_chillan"], m["sin_W7"], m["M5"][0], m["M5"][1] or 0, m["M8"]["n_1mw"], m["veredicto"]))
    print()
    if "informativo" in ruta or ruta.endswith("sin_i4b.json"):
        for s, m in p["por_sensor"].items():
            altas = [x for x in m["M8"]["lista"] if (mw(x) or 0) >= 1.0]
            print("- %s, M8 (publicaciones diurnas de 1 MW o más en pasadas sin fila de MIROVA): %s" % (s, altas))
            print("- %s, protegidas no publicadas: %s" % (s, m.get("protegidas_no_publicadas")))
            print("- %s, por ventana: %s" % (s, m["por_ventana"]))
        print()
