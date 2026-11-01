# Detalle de la discrepancia LAT/LON (píxel más caliente) contra Max_Dist (píxel más lejano) en el OSF v2.5.
# Denominador: filas Npix=1 por resolución (ahí los dos campos DEBERÍAN referirse al mismo píxel).
import sys, io, numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
df = pd.read_csv(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
R = 6371008.8
la1, lo1, la2, lo2 = map(np.radians, (df.LAT, df.LON, df.Volc_LAT, df.Volc_LON))
a = np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
df["dhot"] = 2*R*np.arcsin(np.sqrt(a))
df["dif"] = df.dhot - df.Max_Dist
for res in (1000, 750, 375):
    s = df[(df.Resolution == res) & (df.Npix == 1)]
    q = np.percentile(s.dif, [1, 5, 25, 50, 75, 95, 99])
    print(f"res {res} Npix=1 n={len(s)} dif(dhot-Max_Dist) percentiles 1,5,25,50,75,95,99 = {np.round(q)}")
    # ¿Max_Dist cuantizado a la grilla? múltiplos de la celda
    r = (s.Max_Dist / res) % 1
    print(f"   Max_Dist/celda parte fraccionaria: mediana {np.median(r):.3f}; frac en (0.02,0.98): {100*((r>0.02)&(r<0.98)).mean():.1f} %")
    # control: dhot cuantizado?
    r2 = (s.dhot / res) % 1
    print(f"   dhot/celda parte fraccionaria en (0.02,0.98): {100*((r2>0.02)&(r2<0.98)).mean():.1f} %")
s = df[(df.Resolution == 375)]
print("375 todas: Satellite x dif>188:", s.assign(m=s.dif>188).groupby("Satellite").m.mean().round(4).to_dict())
print("375 todas: Dayflag x dif>188:", s.assign(m=s.dif>188).groupby("Dayflag").m.mean().round(4).to_dict())
