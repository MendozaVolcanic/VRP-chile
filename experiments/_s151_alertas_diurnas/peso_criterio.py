# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 4: cuanto pesan las alertas diurnas en el criterio de victoria.

Une las dos pruebas independientes de real_o_reflejo.py (continuidad de magnitud con las noches vecinas) y
distancia_dia_noche.py (si las detecciones diurnas de MIROVA en ese volcan se amontonan en el crater o se
reparten como el azar) en tres clases por pasada protegida diurna (lectura A):
  - real probable: magnitud consistente con las noches vecinas Y el volcan muestra de dia detecciones
    amontonadas en el crater (fraccion a <= 3 km al menos 10 veces la del azar, tabla CONS, todos los sensores);
  - reflejo o Sol probable: aislada o desproporcionada (la de dia supera en mas de T veces a la noche);
  - indeterminada: consistente en magnitud, pero de dia MIROVA en ese volcan nunca o casi nunca detecta en
    el crater, asi que la distancia OCR (que viene de otra pasada) no basta para ubicarla.
El corte de 10 veces no se ajusta para este estudio: es el orden de magnitud que separa, en
distancia_dia_noche_salida.txt, a los volcanes con actividad nocturna en el crater (45 a 89 veces el azar) del
azar (1 vez); se informa ademas la sensibilidad con 5 y 20.
Tambien cuenta las protegidas diurnas de 50 MW o mas (umbral diurno del conjunto curado de Coppola et al.
2026, Scientific Data, Tabla 1) y compara con las protegidas nocturnas que hoy cuentan los evaluadores,
por sensor y tramo de A119.
Salida: peso_criterio_salida.txt.
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from pipeline.store import _solar_elevation  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from clase_mirova import alerta_protegida, clave_pasada  # noqa: E402

AQUI = Path(__file__).resolve().parent
AZAR = 0.011  # distancia_dia_noche_salida.txt, primera linea


def tramo(fecha):
    if fecha < "2026-03-01":
        return "T0 ene-feb"
    if fecha < "2026-06-13":
        return "T1 mar-12jun"
    return "T2 13jun-oct"


def concentracion_diurna():
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        co = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}
    d = defaultdict(list)
    for f in cargar_referencia_unificada():
        if f["source"] != "CONS" or not f["vrp_mw"] or f["vrp_mw"] <= 0 or f["dist_km"] is None:
            continue
        la, lo = co[f["volcano"]]
        if _solar_elevation(la, lo, datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")) > 0:
            d[f["volcano"]].append(f["dist_km"])
    return {v: (float(np.mean(np.array(x) <= 3.0)) / AZAR, len(x)) for v, x in d.items()}


def main():
    out = []
    p = out.append
    dia = json.load(open(AQUI / "real_o_reflejo_filas.json", encoding="utf-8"))
    pob = json.load(open(AQUI / "poblacion_filas.json", encoding="utf-8"))
    conc = concentracion_diurna()
    p("Concentracion diurna en el crater (veces el azar, n filas diurnas VRP > 0 de la tabla):")
    for v in sorted(conc):
        p("   %-20s %6.1f  (n=%d)" % (v, conc[v][0], conc[v][1]))

    def clase(f, corte):
        if f["clase"] in ("aislada", "desproporcionada"):
            return "reflejo o Sol probable"
        if conc.get(f["volcano"], (0, 0))[0] >= corte:
            return "real probable"
        return "indeterminada"

    # nocturnas protegidas por pasada (lo que hoy cuentan los evaluadores)
    noct = defaultdict(set)
    for f in pob["noche"]:
        if alerta_protegida(f, lectura="A"):
            noct[(f["sensor_bucket"], tramo(f["fecha_utc"]))].add(clave_pasada(f))
    # canal de la pasada diurna: CONS si alguna fila de la pasada es de la tabla
    canal = defaultdict(set)
    for f in pob["dia"]:
        if alerta_protegida(f, lectura="A"):
            canal[clave_pasada(f)].add(f["source"])

    for corte in (10, 5, 20):
        p("\n=== corte de concentracion %d veces el azar ===" % corte)
        c = Counter(clase(f, corte) for f in dia)
        p("Pasadas protegidas diurnas: %d -> %s" % (len(dia), dict(sorted(c.items()))))
        if corte != 10:
            continue
        p("\nPor sensor y tramo A119 (pasadas): protegidas nocturnas que cuentan los evaluadores contra diurnas")
        p("   %-9s %-13s %8s %8s %8s %8s %8s %10s" % ("sensor", "tramo", "noche", "dia", "real", "reflejo", "indet",
                                                     "dia_tabla"))
        tot = Counter()
        llaves = sorted(set(noct) | {(f["sensor_bucket"], tramo(f["fecha_utc"])) for f in dia})
        for k in llaves:
            fs = [f for f in dia if (f["sensor_bucket"], tramo(f["fecha_utc"])) == k]
            cc = Counter(clase(f, corte) for f in fs)
            tab = sum(1 for f in fs if "CONS" in canal[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])])
            fila = (len(noct[k]), len(fs), cc["real probable"], cc["reflejo o Sol probable"], cc["indeterminada"], tab)
            tot.update(dict(zip(("n", "d", "r", "f", "i", "t"), fila)))
            p("   %-9s %-13s %8d %8d %8d %8d %8d %10d" % ((k[0], k[1]) + fila))
        p("   %-23s %8d %8d %8d %8d %8d %10d" % ("TOTAL", tot["n"], tot["d"], tot["r"], tot["f"], tot["i"], tot["t"]))
        p("   sin T0 (enero y febrero no se usan, A119): noche %d, dia %d, real %d"
          % (tot["n"] - sum(len(noct[k]) for k in noct if k[1].startswith("T0")),
             sum(1 for f in dia if not tramo(f["fecha_utc"]).startswith("T0")),
             sum(1 for f in dia if not tramo(f["fecha_utc"]).startswith("T0") and clase(f, corte) == "real probable")))
        p("\nReal probable por volcan: %s" % dict(Counter(f["volcano"] for f in dia if clase(f, corte) == "real probable")))
        p("Indeterminada por volcan: %s" % dict(Counter(f["volcano"] for f in dia if clase(f, corte) == "indeterminada")))
        p("Reflejo o Sol probable por volcan: %s"
          % dict(Counter(f["volcano"] for f in dia if clase(f, corte) == "reflejo o Sol probable")))
        # A94: la unidad del operador es el evento, no la pasada. Una diurna real cuya actividad la replica SI ve
        # en una noche vecina (alerta nocturna de MIROVA del mismo volcan a <= 24 h) no es un evento perdido.
        def th(fe):
            return datetime.strptime(fe[:16], "%Y-%m-%d %H:%M").timestamp() / 3600.0
        noct_t = defaultdict(list)
        noct_tp = defaultdict(list)
        for f in pob["noche"]:
            noct_t[f["volcano"]].append(th(f["fecha_utc"]))
            if alerta_protegida(f, lectura="A"):
                noct_tp[f["volcano"]].append(th(f["fecha_utc"]))
        for nombre in ("real probable", "indeterminada", "reflejo o Sol probable"):
            fs = [f for f in dia if clase(f, corte) == nombre]
            a = sum(1 for f in fs if any(abs(t - th(f["fecha_utc"])) <= 24 for t in noct_t[f["volcano"]]))
            b = sum(1 for f in fs if any(abs(t - th(f["fecha_utc"])) <= 24 for t in noct_tp[f["volcano"]]))
            p("%-24s %3d pasadas: con alerta nocturna de MIROVA a <= 24 h: %d; con alerta nocturna protegida: %d"
              % (nombre, len(fs), a, b))
        g50 = [f for f in dia if f["vrp_mw"] >= 50]
        p("\nProtegidas diurnas de 50 MW o mas (umbral diurno de Coppola et al. 2026, Tabla 1): %d -> %s"
          % (len(g50), ["%s %s %s %.1f MW %s" % (f["fecha_utc"][:16], f["volcano"], f["sensor_bucket"], f["vrp_mw"],
                                                 clase(f, corte)) for f in g50]))
        p("Protegidas diurnas bajo 5 MW (rango de las falsas alertas diurnas de Coppola et al. 2016a, p. 17): %d de %d"
          % (sum(1 for f in dia if f["vrp_mw"] < 5), len(dia)))
    (AQUI / "peso_criterio_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
