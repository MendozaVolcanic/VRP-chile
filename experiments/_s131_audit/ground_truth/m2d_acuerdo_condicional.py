# -*- coding: utf-8 -*-
"""M2d — el único uso del TIF que sobrevive al control: acuerdo CONDICIONAL.

POR QUÉ: el máximo del infrarrojo medio de la escena de MIROVA es bimodal. En una
fracción de las pasadas cae sobre el edificio volcánico; en el resto se va al borde
del recuadro, que es el terreno tibio de baja altitud (A69, visible en el dato de
ELLOS y no sólo en el nuestro). Nada permite predecir a priori en cuál de los dos
modos está una pasada (el z del realce no separa: 33 % de acierto en holdout).

Pero el modo se puede LEER a posteriori en la escena, sin mirar nuestro dato: si el
máximo de MIROVA está a menos de 2 km del cráter, esa pasada es una en que la escena
de ellos ve el volcán. La pregunta que sí se puede contestar con eso es:
**cuando la escena de MIROVA muestra el volcán, ¿nuestro clúster cae en el mismo
lugar?** Es un subconjunto favorable (son las pasadas de señal más fuerte) y hay que
decirlo, pero es evidencia exógena real sobre nuestra posición.

Read-only.
"""
import numpy as np
import pandas as pd

import _lib as L

PIX = {"MODIS": 1000.0, "VIIRS750": 750.0, "VIIRS375": 375.0}


def main():
    d = pd.read_csv(L.OUT + "/m2c_tabla_pasadas.csv")
    d = d[d.tiene_control if "tiene_control" in d else d.tiene_record.astype(bool)]
    det = d[(d.vrp_pc.fillna(0) > 0) & d.pc_a_tif_m.notna()].copy()
    det["cerca"] = det.tif_a_vent_km <= 2.0
    det["pix"] = det.sensor.map(PIX)

    res = {"definicion": "escena de MIROVA 'sobre el volcán' = su máximo de realce "
                         "a <=2 km del cráter; subconjunto favorable, declarado",
           "n_pasadas_con_deteccion_nuestra": int(len(det))}
    tab = {}
    for (s, cerca), g in det.groupby(["sensor", "cerca"]):
        tab[f"{s}|{'tif_sobre_volcan' if cerca else 'tif_al_borde'}"] = dict(
            n=int(len(g)),
            pc_a_tif_m_mediana=round(float(g.pc_a_tif_m.median()), 0),
            pc_a_tif_en_pixeles=round(float((g.pc_a_tif_m / g.pix).median()), 2),
            frac_dentro_2_pixeles=round(float((g.pc_a_tif_m <= 2 * g.pix).mean()), 3),
            pc_a_vent_km_mediana=round(float(g.pc_a_vent_km.median()), 2),
            tif_a_vent_km_mediana=round(float(g.tif_a_vent_km.median()), 2))
    res["por_sensor_y_modo"] = tab
    res["frac_pasadas_tif_sobre_volcan"] = (
        det.groupby("sensor")["cerca"].mean().round(3).to_dict())

    porvol = {}
    for (v, s), g in det[det.cerca].groupby(["volcano", "sensor"]):
        if len(g) < 5:
            continue
        porvol[f"{v}|{s}"] = dict(n=int(len(g)),
                                  pc_a_tif_m_mediana=round(float(g.pc_a_tif_m.median()), 0),
                                  pc_a_tif_px=round(float((g.pc_a_tif_m / g.pix).median()), 2))
    res["por_volcan_modo_sobre_volcan_n>=5"] = porvol
    L.dump("m2d_acuerdo_condicional.json", res)
    print(pd.DataFrame(tab).T.to_string())
    print("\nfrac pasadas con TIF sobre el volcán:", res["frac_pasadas_tif_sobre_volcan"])
    print(pd.DataFrame(porvol).T.to_string())


if __name__ == "__main__":
    main()
