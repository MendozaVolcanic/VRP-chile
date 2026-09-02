# -*- coding: utf-8 -*-
"""M3b — el GATE del control: ¿en qué celdas volcán×sensor el TIF reproduce a MIROVA?

POR QUÉ: el control global (M3) dice que el punto extraído del GeoTIFF no sigue a la
`Distancia_km` que MIROVA publica. Pero "no sirve" en promedio puede esconder "sirve
donde la anomalía es fuerte". El criterio se fija ANTES de mirar el resultado por
volcán, y una celda que no lo pasa queda EXCLUIDA del eje espacial (M2): sin control,
no hay veredicto.

CRITERIO PRE-REGISTRADO (las tres condiciones a la vez):
  1. n >= 10 pasadas con ALERTA de MIROVA y TIF de esa misma pasada;
  2. error mediano |d_estimado - Distancia_km| <= 1,0 km;
  3. el estimador le gana al NULO TRIVIAL ("el punto está en el cráter, dist=0")
     en más del 60 % de las pasadas.

La condición 3 es la que importa: sin ella, un volcán cuyas alertas son todas a
distancia ~0 pasaría el control por el simple hecho de que cualquier estimador que
apunte al cráter acierta.
"""
import numpy as np
import pandas as pd

import _lib as L

EST = "d_realce_3x3_mirova_center"
MIN_N, MAX_ERR, MIN_GANA = 10, 1.0, 0.60


def main():
    d = pd.read_csv(L.OUT + "/m3_control_detalle.csv")
    d = d[d.dist_csv.notna() & d[EST].notna()].copy()
    d["err"] = (d[EST] - d.dist_csv).abs()
    d["err_nulo"] = d.dist_csv.abs()
    d["gana"] = d.err < d.err_nulo

    filas = {}
    for (v, s), g in d.groupby(["volcano", "sensor"]):
        filas[f"{v}|{s}"] = dict(
            n=int(len(g)),
            err_mediano_km=round(float(g.err.median()), 2),
            err_nulo_mediano_km=round(float(g.err_nulo.median()), 2),
            gana_al_nulo=round(float(g.gana.mean()), 2),
            dist_csv_mediana=round(float(g.dist_csv.median()), 2),
            dist_estimada_mediana=round(float(g[EST].median()), 2),
            aprueba=bool(len(g) >= MIN_N and g.err.median() <= MAX_ERR
                         and g.gana.mean() > MIN_GANA))
    por_sensor = {}
    for s, g in d.groupby("sensor"):
        por_sensor[s] = dict(n=int(len(g)),
                             err_mediano_km=round(float(g.err.median()), 2),
                             err_nulo_mediano_km=round(float(g.err_nulo.median()), 2),
                             gana_al_nulo=round(float(g.gana.mean()), 2))
    aprob = [k for k, v in filas.items() if v["aprueba"]]
    res = dict(estimador=EST,
               criterio=dict(min_n=MIN_N, max_err_mediano_km=MAX_ERR,
                             min_frac_gana_al_nulo=MIN_GANA,
                             nulo="el punto caliente está en el cráter (dist=0 km)"),
               n_total=int(len(d)), por_sensor=por_sensor,
               por_volcan_sensor=filas,
               celdas_aprobadas=aprob,
               n_pasadas_en_celdas_aprobadas=int(
                   sum(filas[k]["n"] for k in aprob)),
               veredicto=("el instrumento NO reproduce a MIROVA en general; "
                          f"sólo {len(aprob)} celdas lo pasan"))
    L.dump("m3b_gate.json", res)
    t = pd.DataFrame(filas).T.sort_values(["aprueba", "err_mediano_km"],
                                          ascending=[False, True])
    print(t.to_string())
    print("\npor sensor:"); print(pd.DataFrame(por_sensor).T.to_string())
    print("\naprobadas:", aprob)


if __name__ == "__main__":
    main()
