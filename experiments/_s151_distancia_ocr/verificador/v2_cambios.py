# -*- coding: utf-8 -*-
"""Filas OCR VIIRS375 SIN pasada en la tabla (solo OCR) donde OCR y serie (variante C) caen a distinto lado del limite."""
import sys, pandas as pd, numpy as np
sys.stdout.reconfigure(encoding="utf-8"); pd.set_option("display.width", 250)
X = pd.read_csv("C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/ocr_vs_serie.csv")
Y = X[X.C_clase.notna() & X.d_tab.isna()]
print("solo OCR con imagen:", len(Y), "por tramo", Y.tramo.value_counts().sort_index().to_dict())
d = Y[Y.C_dec.isin(["cerca", "lejos"])]; cb = d[d.C_dec != d.real_ocr]
print("decididas", len(d), "cambian de lado", len(cb), "| con firma otra pasada:", int((cb.otra_tab | cb.C_prespost).sum()))
print("cambios por volcan:", cb.vol.value_counts().to_dict())
print(cb[["vol", "t", "tramo", "ocr", "C_clase", "C_est", "C_kmin", "C_kmax", "C_kmcol", "otra_tab", "C_prespost", "A_dec"]].to_string())
