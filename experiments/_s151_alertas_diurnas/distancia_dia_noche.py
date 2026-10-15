# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 2: donde caen las detecciones de MIROVA de dia, contra el azar.

EL FENOMENO. El calor volcanico tiene domicilio: el crater. Un reflejo solar en una nube, o un salar o
una ladera que el Sol calienta, puede aparecer en cualquier parte de la escena de 51 x 51 km. Si las
detecciones diurnas de MIROVA (toda fila de la tabla con VRP > 0, sea ALERTA dentro del radio del
scraper o FALSO_POSITIVO fuera) se reparten por la escena como el azar, las pocas que caen cerca del
crater no dicen nada del volcan: son la cola de un campo aleatorio. Si se amontonan en el crater, hay
algo ahi.

QUE SE MIDE. Solo la TABLA (canal CONS), porque la distancia del OCR puede ser de otra pasada
(reference_ocr_imagen_de_otra_pasada). Por volcan y sensor, la fraccion de filas con VRP > 0 a <= 3 km
del punto de referencia de MIROVA, de dia y de noche, contra la fraccion que daria el azar: puntos
uniformes en el cuadrado de 51 x 51 km centrado (grilla MIROVA, A4), con la misma distancia maxima
observada recortada.
Control que puede fallar: de noche la fraccion a <= 3 km debe superar con holgura al azar en los volcanes
con actividad conocida (Lascar, Villarrica, Nevados de Chillan en erupcion). Si no la supera, la distancia
de la tabla no sirve para esto.
Salida: distancia_dia_noche_salida.txt.
"""
from __future__ import annotations

import io
import os
import sys
from collections import defaultdict
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

AQUI = Path(__file__).resolve().parent
RNG = np.random.default_rng(113)
CORTE_KM = 3.0


def frac_azar(corte, dmax, n=400000):
    x = RNG.uniform(-25.5, 25.5, n)
    y = RNG.uniform(-25.5, 25.5, n)
    d = np.hypot(x, y)
    d = d[d <= dmax]
    return float(np.mean(d <= corte))


def main():
    out = []
    p = out.append
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        co = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}
    g = defaultdict(list)
    for f in cargar_referencia_unificada():
        if f["source"] != "CONS" or not f["vrp_mw"] or f["vrp_mw"] <= 0 or f["dist_km"] is None:
            continue
        la, lo = co[f["volcano"]]
        e = _solar_elevation(la, lo, datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M"))
        luz = "dia" if e > 0 else "noche"
        g[(f["volcano"], f["sensor_bucket"], luz)].append(f["dist_km"])
        g[("TODOS", f["sensor_bucket"], luz)].append(f["dist_km"])
    dmax = max(max(v) for v in g.values())
    azar = frac_azar(CORTE_KM, dmax)
    p("Tabla (CONS), filas con VRP > 0. Distancia maxima observada: %.1f km. Fraccion a <= %.0f km que da el azar"
      " (uniforme en 51 x 51 km recortado a esa distancia): %.3f" % (dmax, CORTE_KM, azar))
    p("   %-20s %-9s %-6s %5s %10s %10s %12s" % ("volcan", "sensor", "luz", "n", "<=3 km", "mediana", "veces azar"))
    for k in sorted(g):
        d = np.array(g[k])
        if len(d) < 5:
            continue
        fr = float(np.mean(d <= CORTE_KM))
        p("   %-20s %-9s %-6s %5d %10.3f %10.2f %12.1f" % (k[0], k[1], k[2], len(d), fr, np.median(d), fr / azar))
    (AQUI / "distancia_dia_noche_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
