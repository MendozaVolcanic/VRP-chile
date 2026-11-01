# -*- coding: utf-8 -*-
"""P2 (S159). Los cortes de Npix donde las filas V750 sobre 50 grados dejan de cumplir VRP = dL x k coinciden con
los cortes del tamano de dilatacion de MIROVA_VIIRS750_VRP.m l. 68-74 (npix <= 4 -> 3; <= 30 -> 5; > 30 -> 7)?
Pregunta 1: si no hubiera relacion, la fraccion que cumple variaria suave con Npix, sin salto en 4|5 ni en 30|31.
Pregunta 2 / control negativo: el mismo barrido bajo 50 grados debe dar 1,0 en todos los Npix (ra2/03).
Ventana: todo el OSF v2.5, global, noche y dia juntos; tolerancia 1 %."""
import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
o = pd.read_csv(OSF, usecols=["Satellite", "Resolution", "SatZen", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "Dayflag"])
v = o[(o.Resolution == 750)].copy()
v["cumple"] = ((v.VRP / ((v.Tot_Lmir_hot - v.Tot_Lmir_bk) * 1.97e7 * 0.5625)) - 1).abs() <= 1e-2
for nombre, s in [("SOBRE 50", v[v.SatZen >= 50]), ("BAJO 50 (control)", v[v.SatZen < 50])]:
    print(f"\n=== V750 {nombre}: fraccion que cumple por Npix exacto (n) ===")
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 28, 29, 30, 31, 32, 33]:
        x = s[s.Npix == n]
        print(f"Npix={n:3d}  cumple={x.cumple.mean() if len(x) else float('nan'):.4f}  n={len(x)}")
