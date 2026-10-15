# -*- coding: utf-8 -*-
"""Arbitro de tres vias: filas OCR con distancia > 0 que tienen la MISMA pasada en la tabla (+-3 min, distancia de
latest.php). Quien acierta cuando OCR y serie discrepan: el OCR o la lectura de la serie? Usa v2/ocr_vs_serie.csv."""
import sys, numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
X = pd.read_csv("C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/ocr_vs_serie.csv")
for var in "AC":
    Y = X[X[f"{var}_clase"].notna() & X.d_tab.notna()].copy()
    Y["lado_tab"] = [("cerca" if d <= LIM.get(v, 5.0) else "lejos") for d, v in zip(Y.d_tab, Y.vol)]
    Y["e_ocr"] = (Y.ocr - Y.d_tab).abs()
    def e_serie(r):
        cl = r[f"{var}_clase"]; d = min(r.d_tab, 25)
        if cl == "unico": return abs(r[f"{var}_est"] - d)
        if cl in ("solapado", "ambiguo"): return max(0, r[f"{var}_kmin"] - d, d - r[f"{var}_kmax"])
        return np.nan
    Y["e_serie"] = Y.apply(e_serie, axis=1)
    print(f"\n== variante {var}: filas OCR VIIRS375 con imagen y con la misma pasada en la tabla: {len(Y)}")
    for tr, g in Y.groupby("tramo"):
        print(f"  {tr}: n={len(g)} | OCR vs tabla >2km {int((g.e_ocr>2).sum())} | serie vs tabla >2km {int((g.e_serie>2).sum())} (sin dato {int(g.e_serie.isna().sum())})"
              f" | OCR cambia de lado vs tabla {int((g.real_ocr!=g.lado_tab).sum())} | serie decide y yerra vs tabla {int((g[f'{var}_dec'].isin(['cerca','lejos']) & (g[f'{var}_dec']!=g.lado_tab)).sum())} de {int(g[f'{var}_dec'].isin(['cerca','lejos']).sum())}")
    m = Y[(Y.e_ocr > 2)]
    print("  filas donde el OCR discrepa de la tabla > 2 km:")
    print(m[["vol", "t", "tipo", "ocr", "d_tab", f"{var}_clase", f"{var}_est", f"{var}_kmin", f"{var}_kmax", "otra_tab", f"{var}_prespost"]].to_string())
# tipo de las tablas duplicadas: VRP de la tabla
