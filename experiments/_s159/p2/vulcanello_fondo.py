# -*- coding: utf-8 -*-
"""P2 (S159). Campus et al. 2024 describe el fondo de VIIRS 375 de dos maneras (p. 3, Ec. 2: media de los vecinos de
cada alertado, sumada; p. 4, Tabla 1: «measured in the Vulcanello area»). S141 D-07 lo dejo SIN RESOLVER. Los dos
archivos del propio paper (OSF jepv6, S1 y S2) permiten decidirlo: si L_MIRbk fuera Npix x radiancia del pixel fijo de
Vulcanello, entonces L_MIRbk/Npix = Planck(I4, BT_background de S2 en la misma pasada) con dispersion chica.
Pregunta 1: si la Tabla 1 fuera literal, la razon (L_MIRbk/Npix)/Planck(BT_bg) daria ~1 con dispersion de pocos %;
si el fondo es local (vecinos del alertado), la razon se despega y depende de la pasada.
Pregunta 2 / control positivo: con Npix = 1, L_MIRhot contra Planck(BT_center) de S2 (el pixel de Gran Cratere suele
ser el alertado) debe dar razon ~1 en la mayoria; si el pareo de fechas o la funcion de Planck estuvieran rotos, el
control positivo tambien se despegaria. Longitud de onda efectiva I4: 3,74 um (Campus 2024 p. 3, renderizada).
Ventana: 2021-03-01 a 2023-03-01 (todo S1, 354 filas). Los CSV no tienen licencia declarada: se leen, no se copian.
"""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\vrp-trabajo\s159-pruebas\data\mirova_reference\campus2024_vulcano"
s1 = pd.read_csv(D + r"\S1_MIROVA_Vulcano.csv"); s1.columns = ["fecha", "cenit", "az", "npix", "lhot", "lbk", "vrp"]
s2 = pd.read_csv(D + r"\S2_MIROVA_Vulcano.csv"); s2.columns = ["fecha", "bt_c", "bt_bg"]
for d in (s1, s2):
    d["fecha"] = pd.to_datetime(d.fecha, format="%d/%m/%y %H:%M")
h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
def planck(T, lam_um=3.74):
    lam = lam_um * 1e-6
    return 2 * h * c**2 / lam**5 / (np.exp(h * c / (lam * k * T)) - 1) * 1e-6  # W m-2 sr-1 um-1
m = s1.merge(s2, on="fecha", how="left")
print("filas S1:", len(s1), "| con pareo exacto en S2:", int(m.bt_bg.notna().sum()))
m = m[m.bt_bg.notna()].copy()
m["r_bg"] = (m.lbk / m.npix) / planck(m.bt_bg)
m["r_bgc"] = (m.lbk / m.npix) / planck(m.bt_c)
print("\nPRUEBA: (L_MIRbk/Npix) / Planck(I4, BT_background Vulcanello)")
print(m.r_bg.describe(percentiles=[.05, .25, .5, .75, .95]).round(4).to_string())
print("fraccion con |razon-1| <= 2 %:", round(((m.r_bg - 1).abs() <= 0.02).mean(), 4))
print("\nreferencia: (L_MIRbk/Npix) / Planck(I4, BT_center Gran Cratere)")
print(m.r_bgc.describe(percentiles=[.05, .5, .95]).round(4).to_string())
one = m[m.npix == 1]
r_hot = one.lhot / planck(one.bt_c)
print(f"\nCONTROL POSITIVO (Npix=1, n={len(one)}): L_MIRhot / Planck(BT_center)")
print(r_hot.describe(percentiles=[.05, .25, .5, .75, .95]).round(4).to_string())
print("fraccion con |razon-1| <= 2 %:", round(((r_hot - 1).abs() <= 0.02).mean(), 4))
print("\ncorrelacion de Pearson entre L_MIRbk/Npix y Planck(BT_bg):", round(np.corrcoef(m.lbk / m.npix, planck(m.bt_bg))[0, 1], 4))
print("correlacion entre L_MIRbk/Npix y Planck(BT_center):", round(np.corrcoef(m.lbk / m.npix, planck(m.bt_c))[0, 1], 4))
