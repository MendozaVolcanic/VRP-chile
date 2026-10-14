# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 4: cuanto pesan las alertas diurnas en el criterio de victoria.

Une dos pruebas: real_o_reflejo.py (continuidad de magnitud con las noches vecinas) y la concentracion de las
detecciones diurnas de la TABLA de MIROVA en el crater del mismo volcan (fraccion a <= 3 km contra el azar, 1,1 %).

CORRECCION S151 (verificador con contexto limpio del PR #812). La primera version calculaba la concentracion con
TODAS las filas diurnas de la tabla, incluidas las de las mismas pasadas que se estaban clasificando: circular.
Ahora se calcula de dos maneras no circulares:
  - sin ninguna pasada protegida diurna (todas fuera; es la medida que decide la clase);
  - dejando fuera solo la propia pasada (leave-one-out, como sensibilidad).
La version circular se imprime solo para mostrar cuanto se movia.
Las pasadas que solo tienen fila OCR no traen distancia propia (la del OCR es de otra pasada,
reference_ocr_imagen_de_otra_pasada): heredan la concentracion de su volcan, no tienen una propia.

Clases por pasada protegida diurna (lectura A):
  - real probable: magnitud consistente Y concentracion diurna no circular >= corte (se informan 5, 10 y 20);
  - reflejo o Sol probable: aislada o desproporcionada en magnitud;
  - SIN EVIDENCIA: consistente en magnitud pero sin concentracion diurna que la confirme.

A119 en el denominador: una pasada cuenta solo si es desde el 2026-06-13 (deciden tabla y OCR) o si es del
2026-03-01 al 2026-06-12 y tiene fila en la tabla (ahi el OCR no decide). Enero y febrero no se usan.
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

import yaml  # noqa: E402

from pipeline.store import _solar_elevation  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from clase_mirova import alerta_protegida, clave_pasada  # noqa: E402

AQUI = Path(__file__).resolve().parent
AZAR = 0.011  # distancia_dia_noche_salida.txt, primera linea
CORTES = (5, 10, 20)


def tramo(fecha):
    if fecha < "2026-03-01":
        return "T0 ene-feb"
    if fecha < "2026-06-13":
        return "T1 mar-12jun"
    return "T2 13jun-oct"


def usable_a119(fecha, canales):
    t = tramo(fecha)
    return t == "T2 13jun-oct" or (t == "T1 mar-12jun" and "CONS" in canales)


def th(fe):
    return datetime.strptime(fe[:16], "%Y-%m-%d %H:%M").timestamp() / 3600.0


def filas_diurnas_tabla():
    """Filas diurnas de la tabla con VRP > 0 y distancia: (volcan, clave de pasada, distancia)."""
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        co = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}
    out = []
    alertas_tabla_dia = []
    for f in cargar_referencia_unificada():
        if f["source"] != "CONS":
            continue
        la, lo = co[f["volcano"]]
        if _solar_elevation(la, lo, datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")) <= 0:
            continue
        if f["tipo"] == "ALERTA_TERMICA":
            alertas_tabla_dia.append(f)
        if not f["vrp_mw"] or f["vrp_mw"] <= 0 or f["dist_km"] is None:
            continue
        out.append((f["volcano"], clave_pasada(f), f["dist_km"]))
    return out, alertas_tabla_dia


def conc(filas, volcan, excluir):
    d = [x[2] for x in filas if x[0] == volcan and x[1] not in excluir]
    if not d:
        return 0.0, 0
    return sum(1 for x in d if x <= 3.0) / len(d) / AZAR, len(d)


def main():
    out = []
    p = out.append
    dia = json.load(open(AQUI / "real_o_reflejo_filas.json", encoding="utf-8"))
    pob = json.load(open(AQUI / "poblacion_filas.json", encoding="utf-8"))
    filas, alertas_tabla_dia = filas_diurnas_tabla()

    canal = defaultdict(set)
    for f in pob["dia"]:
        if alerta_protegida(f, lectura="A"):
            canal[clave_pasada(f)].add(f["source"])
    prot_dia = set(canal)
    for f in dia:
        f["clave"] = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
        f["canales"] = canal[f["clave"]]

    vols = sorted({x[0] for x in filas})
    p("Concentracion diurna en el crater (veces el azar; n filas diurnas VRP > 0 de la tabla)")
    p("   %-20s %18s %26s" % ("volcan", "circular (todas)", "sin pasadas protegidas dia"))
    conc_nc = {}
    for v in vols:
        a, na = conc(filas, v, set())
        b, nb = conc(filas, v, prot_dia)
        conc_nc[v] = b
        p("   %-20s %10.1f (n=%3d) %16.1f (n=%3d)" % (v, a, na, b, nb))

    for f in dia:
        f["conc_loo"] = conc(filas, f["volcano"], {f["clave"]})[0]
        f["conc_nc"] = conc_nc.get(f["volcano"], 0.0)

    def clase(f, corte, cual="conc_nc"):
        if f["clase"] in ("aislada", "desproporcionada"):
            return "reflejo o Sol probable"
        if f[cual] >= corte:
            return "real probable"
        return "SIN EVIDENCIA"

    p("\nClases de las %d pasadas protegidas diurnas:" % len(dia))
    for corte in CORTES:
        p("   corte %2d, sin pasadas protegidas: %s" % (corte, dict(sorted(Counter(clase(f, corte) for f in dia).items()))))
        p("   corte %2d, leave-one-out:          %s" % (corte, dict(sorted(Counter(clase(f, corte, "conc_loo")
                                                                                      for f in dia).items()))))
    solo_ocr = [f for f in dia if f["canales"] == {"OCR"}]
    p("Pasadas solo OCR (sin distancia propia; heredan la concentracion de su volcan): %d de %d"
      % (len(solo_ocr), len(dia)))

    # A119 en el denominador, igual para el dia y para la noche
    corte = 10
    canal_n = defaultdict(set)
    for f in pob["noche"]:
        if alerta_protegida(f, lectura="A"):
            canal_n[clave_pasada(f)].add(f["source"])
    p("\nA119 aplicado (desde 2026-06-13 todo; marzo al 12 de junio solo con fila en la tabla; ene-feb fuera)")
    p("   %-9s %-13s %10s %10s %10s %10s %10s" % ("sensor", "tramo", "noche_A119", "dia_total", "dia_A119",
                                                 "reflejo", "sin_evid."))
    tot = Counter()
    llaves = sorted({(k[1], tramo(k[2])) for k in canal_n} | {(f["sensor_bucket"], tramo(f["fecha_utc"])) for f in dia})
    for s, tr in llaves:
        nn = sum(1 for k, c in canal_n.items() if k[1] == s and tramo(k[2]) == tr and usable_a119(k[2], c))
        fs = [f for f in dia if f["sensor_bucket"] == s and tramo(f["fecha_utc"]) == tr]
        fu = [f for f in fs if usable_a119(f["fecha_utc"], f["canales"])]
        cc = Counter(clase(f, corte) for f in fu)
        fila = (nn, len(fs), len(fu), cc["reflejo o Sol probable"], cc["SIN EVIDENCIA"] + cc["real probable"])
        tot.update(dict(zip("ntufs", fila)))
        p("   %-9s %-13s %10d %10d %10d %10d %10d" % ((s, tr) + fila))
    p("   %-23s %10d %10d %10d %10d %10d" % ("TOTAL", tot["n"], tot["t"], tot["u"], tot["f"], tot["s"]))
    p("   (sin_evid. junta 'real probable' y 'SIN EVIDENCIA': con la concentracion no circular no hay reales)")
    fu = [f for f in dia if usable_a119(f["fecha_utc"], f["canales"])]
    p("   usables por A119: %d (%d de tabla hasta el 12 de junio, %d desde el 13 de junio)" % (
        len(fu), sum(1 for f in fu if tramo(f["fecha_utc"]) == "T1 mar-12jun"),
        sum(1 for f in fu if tramo(f["fecha_utc"]) == "T2 13jun-oct")))
    p("   por volcan: %s" % dict(sorted(Counter(f["volcano"] for f in fu).items())))

    # A94: la unidad del operador es el evento. Advertencia: esta prueba NO discrimina real de reflejo.
    noct_t, noct_tp = defaultdict(list), defaultdict(list)
    for f in pob["noche"]:
        noct_t[f["volcano"]].append(th(f["fecha_utc"]))
        if alerta_protegida(f, lectura="A"):
            noct_tp[f["volcano"]].append(th(f["fecha_utc"]))
    p("\nAlerta nocturna de MIROVA del mismo volcan a <= 24 h (no discrimina: la cumplen tambien los reflejos)")
    for nombre in ("real probable", "SIN EVIDENCIA", "reflejo o Sol probable"):
        fs = [f for f in dia if clase(f, corte) == nombre]
        a = sum(1 for f in fs if any(abs(t - th(f["fecha_utc"])) <= 24 for t in noct_t[f["volcano"]]))
        b = sum(1 for f in fs if any(abs(t - th(f["fecha_utc"])) <= 24 for t in noct_tp[f["volcano"]]))
        p("   %-24s %3d pasadas: con alerta nocturna: %d; con alerta nocturna protegida: %d" % (nombre, len(fs), a, b))

    g50 = [f for f in dia if f["vrp_mw"] >= 50]
    p("\nProtegidas diurnas de 50 MW o mas (umbral diurno del conjunto CURADO de Coppola et al. 2026, no del NRT): %d -> %s"
      % (len(g50), ["%s %s %.1f MW" % (f["fecha_utc"][:16], f["volcano"], f["vrp_mw"]) for f in g50]))
    p("Alertas diurnas de la TABLA NRT (ALERTA_TERMICA): %d, VRP maximo %.2f MW"
      % (len(alertas_tabla_dia), max(f["vrp_mw"] or 0 for f in alertas_tabla_dia)))
    p("Protegidas diurnas bajo 5 MW: %d de %d; bajo 10 MW: %d de %d"
      % (sum(1 for f in dia if f["vrp_mw"] < 5), len(dia), sum(1 for f in dia if f["vrp_mw"] < 10), len(dia)))
    (AQUI / "peso_criterio_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
