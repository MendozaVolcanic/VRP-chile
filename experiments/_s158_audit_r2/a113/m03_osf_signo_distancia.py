# M03: en el OSF v2.5, ¿hay VRP negativos (sin recorte de deltaL) y que tan lejos llegan los pixeles sumados?
# Fisica: si MIROVA recortara deltaL a cero por pixel, ningun VRP de pasada podria ser negativo;
#   si sumara solo el cumulo del crater, Max_Dist quedaria acotado a pocos km.
# Pregunta 1: un recorte por pixel o un filtro por distancia darian 0 negativos / Max_Dist chico; lo veriamos.
# Pregunta 2: el conteo de negativos se imprime junto al total y al minimo; un cero con n>0 y min>0 es dato,
#   no ausencia de medicion. Control positivo: el minimo y maximo de VRP impresos.
# Denominador: filas del OSF 2025 (archivo 2000-2025) con Npix>0, por Resolution.
import pandas as pd, numpy as np
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(p)
for res in (750,375,1000):
    s = d[(d.Resolution==res)&(d.Npix>0)]
    neg = (s.VRP<0).sum(); dl = (s.Tot_Lmir_hot - s.Tot_Lmir_bk)
    print(f"Res {res}: n={len(s)} VRP<0: {neg} ({100*neg/len(s):.3f} %)  VRP min={s.VRP.min():.1f} max={s.VRP.max():.3e}  deltaL<0: {(dl<0).sum()}")
    print("   Max_Dist (m?) percentiles 50,90,99,max:", np.percentile(s.Max_Dist,[50,90,99]).round(0), s.Max_Dist.max())
    print("   class:", s['class'].value_counts().to_dict())
