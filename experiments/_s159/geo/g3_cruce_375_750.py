# -*- coding: utf-8 -*-
"""S159 frente GEO, parte G: los encabezados de los TIF UTM dicen que la grilla de 750 m esta corrida 187,5 m al
oeste y 187,5 m al sur respecto de la de 375 m (g1). Esto comprueba con los VALORES, no con el encabezado, que el
encabezado no miente: toma el TIF de VIIRS 375 (I4) como campo de muestras y busca, con g2_ajuste_grilla, el
desfase que mejor reproduce el TIF de VIIRS 750 (M13) de la MISMA adquisicion (mismo acquisition_utc y mismo
volcan). Si el encabezado es fiel, el desfase extra es ~0. Si los datos fueran en realidad 2 x 2 de la grilla de
375 con el encabezado mal puesto, el desfase saldria cerca de (+187,5, +187,5).

Ademas reporta el valor de cada TIF y su temperatura de brillo equivalente si fuera radiancia espectral a 3,74 um
(I4) o 4,05 um (M13), para ver si la variable es radiancia.

Las dos preguntas del instrumento:
1. Si el encabezado estuviera corrido, el ajuste lo veria: g2 recupera desfases conocidos de 100 m en el sintetico
   (g2_prueba_ajuste_salida.txt). Aqui el control positivo es correr el mismo ajuste con el encabezado de 750
   corrido a proposito (+187,5, +187,5): debe devolver ~(-187,5, -187,5).
2. Si no hubiera relacion entre los dos TIF (otra pasada, nube), el costo seria cercano a 1 y se declara SIN DATO.
I4 y M13 son bandas distintas (3,74 y 4,05 um): el ajuste afin absorbe la escala; el costo no baja de cero.
Uso: python -I g3_cruce_375_750.py <inventario r1 csv> <carpeta descargas>
"""
import io
import os
import sys

import numpy as np
import pandas as pd
import rasterio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g2_ajuste_grilla as g2  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C1, C2 = 1.191042e8, 1.4387752e4


def bt(L, lam):
    return C2 / (lam * np.log(1 + C1 / (lam ** 5 * L)))


def leer(p):
    with rasterio.open(p) as s:
        return s.read(1).astype(float), s.transform


def main(inv_csv, desc):
    d = pd.read_csv(inv_csv)
    u = d[d.epsg.notna() & (d.epsg != 4326) & d.acquisition_utc.notna()]
    pares = u[u.sensor.isin(["VIIRS375", "VIIRS750"])].groupby(["volcano", "acquisition_utc"])
    filas = []
    for (vol, acq), gg in pares:
        if set(gg.sensor) != {"VIIRS375", "VIIRS750"}:
            continue
        r375 = gg[gg.sensor == "VIIRS375"].iloc[0]
        r750 = gg[gg.sensor == "VIIRS750"].iloc[0]
        if r375.md5_indice == r750.md5_indice:
            continue
        a3, t3 = leer(os.path.join(desc, r375.tif_path))
        a7, t7 = leer(os.path.join(desc, r750.tif_path))
        X3, Y3 = g2.centros(t3.c, t3.f, t3.a, a3.shape[1], a3.shape[0])
        ok = np.isfinite(a3) & (a3 > 0)
        fila = dict(volcano=vol, acq=acq, med375=np.nanmedian(a3[ok]), med750=np.nanmedian(a7[a7 > 0]))
        fila["bt375_K"] = bt(fila["med375"], 3.74)
        fila["bt750_K"] = bt(fila["med750"], 4.05)
        for etiqueta, ox, oy in (("encabezado", 0.0, 0.0), ("control_corrido", 187.5, 187.5)):
            _, res = g2.ajustar(X3[ok], Y3[ok], a3[ok], a7, t7.c + ox, t7.f + oy, t7.a,
                                paso_grueso=75.0, paso_fino=7.5)
            m = res["mejor"]
            fila[f"{etiqueta}_interp"] = m["interp"]
            fila[f"{etiqueta}_dx"] = m["dx"]
            fila[f"{etiqueta}_dy"] = m["dy"]
            fila[f"{etiqueta}_costo"] = round(m["costo"], 3)
        filas.append(fila)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in fila.items()}, flush=True)
    t = pd.DataFrame(filas)
    print("\npares de la misma adquisicion con md5 distinto:", len(t))
    if len(t):
        print("costo <= 0,5 (relacion medible):", int((t.encabezado_costo <= 0.5).sum()))
        b = t[t.encabezado_costo <= 0.5]
        print("desfase con el encabezado, mediana (dx, dy):", b.encabezado_dx.median(), b.encabezado_dy.median())
        print("desfase con el control corrido, mediana (dx, dy):", b.control_corrido_dx.median(),
              b.control_corrido_dy.median())
        print("temperatura de brillo equivalente de la mediana, K: I4", round(t.bt375_K.median(), 1),
              "M13", round(t.bt750_K.median(), 1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
