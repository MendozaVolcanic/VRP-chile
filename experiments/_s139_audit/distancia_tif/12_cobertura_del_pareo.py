# -*- coding: utf-8 -*-
"""S139 - cuántas filas de la web tienen TIF y cuántas no (punto 1 del encargo).

El denominador son las filas ALERTA_TERMICA y FALSO_POSITIVO con VRP > 0 del CSV
consolidado; el numerador, las que emparejan con un TIF del índice REMOTO del archivo
(±30 min, mismo volcán y sensor). Se declara noche y día por separado, porque las alertas
diurnas de MIROVA son en buena parte artefacto de reflexión solar (A76).

Read-only. Usa el índice remoto ya descargado, no baja nada.
"""
import io
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
DL = os.path.join(AQUI, "_dl_")
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")
ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}
SENS = {"MODIS": "MODIS", "VIIRS750": "VIIRS", "VIIRS375": "VIIRS375"}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
    "NevadosDeChillan": {"NevadosDeChillan", "Nevados de Chillan", "Nevados de Chillán"},
    "Copahue": {"Copahue"}, "Llaima": {"Llaima"}, "Lastarria": {"Lastarria"},
    "Isluga": {"Isluga"}, "Chaiten": {"Chaiten", "Chaitén"},
    "Tupungatito": {"Tupungatito"},
}
WEB2OURS = {n: k for k, s in ALIAS.items() for n in s}
LON = {"Villarrica": -71.93, "PlanchonPeteroa": -70.57, "Lascar": -67.73,
       "PuyehueCordonCaulle": -72.12, "NevadosDeChillan": -71.38, "Copahue": -71.18,
       "Llaima": -71.73, "Lastarria": -68.51, "Isluga": -68.83, "Chaiten": -72.65,
       "Tupungatito": -69.80}


def main():
    idx = pd.read_csv(os.path.join(DL, "index_remoto.csv"))
    idx["volcano"] = idx.volcano.map(lambda v: ARCH2OURS.get(v, v))
    acq = pd.to_datetime(idx.acquisition_utc, utc=True, errors="coerce")
    fn = pd.to_datetime(idx.tif_path.str.extract(r"(\d{8}_\d{6})", expand=False),
                        format="%Y%m%d_%H%M%S", utc=True, errors="coerce")
    idx["acq"] = acq.fillna(fn)
    idx = idx.dropna(subset=["acq"])
    idx["sw"] = idx.sensor.map(SENS)

    w = pd.read_csv(WEB)
    w["t"] = pd.to_datetime(w.Fecha_Satelite_UTC, errors="coerce", utc=True)
    w["vol"] = w.Volcan.map(lambda v: WEB2OURS.get(str(v).strip()))
    w["VRP_MW"] = pd.to_numeric(w.VRP_MW, errors="coerce")
    w = w.dropna(subset=["t", "vol"])
    w = w[w.Tipo_Registro.isin(["ALERTA_TERMICA", "FALSO_POSITIVO"]) & (w.VRP_MW > 0)]
    hs = (w.t.dt.hour + w.t.dt.minute / 60.0 + w.vol.map(LON) / 15.0) % 24
    w["noche"] = (hs >= 19) | (hs < 6)
    # Ventana del archivo remoto.
    V0, V1 = idx.acq.min(), idx.acq.max()
    w = w[(w.t >= V0) & (w.t <= V1)]

    hit = []
    for _, r in w.iterrows():
        c = idx[(idx.volcano == r["vol"]) & (idx.sw == r["Sensor"])]
        if c.empty:
            hit.append(False)
            continue
        dt = (c.acq - r["t"]).abs().dt.total_seconds() / 60.0
        hit.append(bool(dt.min() <= 30))
    w = w.assign(con_tif=hit)

    def tabla(g):
        return {"n": int(len(g)), "con_tif": int(g.con_tif.sum()),
                "sin_tif": int((~g.con_tif).sum()),
                "cobertura_pct": round(100.0 * float(g.con_tif.mean()), 1)}

    R = {"_meta": {
        "ventana_archivo_remoto": [str(V0), str(V1)],
        "denominador": "filas ALERTA_TERMICA o FALSO_POSITIVO con VRP_MW>0 del CSV "
                       "consolidado, dentro de la ventana del archivo",
        "tolerancia_min": 30,
        "limite": "el archivo de TIF es un poller de ~1 h: una pasada que MIROVA sobrescribió "
                  "antes de la captura no está, así que la cobertura es una cota inferior "
                  "de lo que MIROVA publicó (mismo argumento que S128)."},
        "global": tabla(w),
        "por_etiqueta": {t: tabla(g) for t, g in w.groupby("Tipo_Registro")},
        "por_sensor": {s: tabla(g) for s, g in w.groupby("Sensor")},
        "noche_dia": {("noche" if k else "dia"): tabla(g) for k, g in w.groupby("noche")},
        "por_sensor_y_etiqueta_noche": {
            f"{s}|{t}": tabla(g) for (s, t), g in
            w[w.noche].groupby(["Sensor", "Tipo_Registro"])}}
    out = os.path.join(AQUI, "12_cobertura_del_pareo.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
    print("escrito:", out)


if __name__ == "__main__":
    main()
