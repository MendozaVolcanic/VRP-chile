# -*- coding: utf-8 -*-
"""Cerca/lejos (limite real por volcan) para las ALERTA_TERMICA_OCR VIIRS 375 con 0 fijo cubiertas por la muestra."""
import sys, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
x = pd.read_csv(sys.argv[1] + "/cero_fijo.csv")
def dec(r):
    if r.clase in ("sin_imagen", "sin_marcador"): return r.clase
    U = LIM.get(r.vol, 5.0); lo, hi = (r.est, r.est) if r.clase == "unico" else (r.kmin, r.kmax)
    return "cerca" if hi < U - 0.6 else ("lejos" if lo > U + 0.6 else "indecidible")
x["dec"] = x.apply(dec, axis=1)
print("filas", len(x), "| decision:", x.dec.value_counts().to_dict())
print("lejos por volcan:", x[x.dec == "lejos"].groupby("vol").size().to_dict())
