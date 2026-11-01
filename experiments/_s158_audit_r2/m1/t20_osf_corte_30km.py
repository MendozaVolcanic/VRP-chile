# M1 T20. Recuento propio de F6-H2 (Max_Dist del OSF nunca pasa de 30 km en ningun sensor). Pregunta 1: si el corte no
# existiera, habria filas sobre 30000 m; pregunta 2: control = Max_Dist tiene distribucion amplia (no constante) y la
# grilla de 750 m SI permite hasta 33.9 km (esquina) segun la geometria 67x67 (33*0.75*sqrt2=35.0 desde el centro).
import pandas as pd,numpy as np
p=r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'
d=pd.read_csv(p,usecols=['Resolution','Max_Dist','Npix'])
for r,g in d.groupby('Resolution'):
    m=g.Max_Dist
    print(f'Resolution {r}: n={len(g)} max={m.max():.1f} m | filas >30000: {(m>30000).sum()} | en (29000,30000]: {((m>29000)&(m<=30000)).sum()} | en (28000,29000]: {((m>28000)&(m<=29000)).sum()} | exactamente 30000: {(m==30000).sum()} | mediana {m.median():.0f}')
print('esquina teorica de 67x67 a 750 m desde el centro (33 celdas en x e y):',round(33*0.75*np.sqrt(2),2),'km')
