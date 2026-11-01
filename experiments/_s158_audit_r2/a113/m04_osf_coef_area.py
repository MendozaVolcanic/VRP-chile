# M04: el VRP de VIIRS 750 del OSF v2.5, ¿sale de deltaL x 1,97e7 x 0,5625 (codigo) o de otra area (0,75e6 m2 del cap. 2025)?
# Pregunta 1: si MIROVA usara area 0,75 km2 o coeficiente distinto, la razon recomputado/OSF se alejaria de 1 en bloque.
# Pregunta 2: control positivo = se imprime tambien la razon con area 0,75 (debe dar 0,75 si el codigo manda).
# Denominador: filas Resolution 750 con Npix>0 del OSF (2012-2025).
import pandas as pd, numpy as np
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(p); s = d[(d.Resolution==750)&(d.Npix>0)].copy()
dl = s.Tot_Lmir_hot - s.Tot_Lmir_bk
for A in (0.5625, 0.75):
    r = dl*1.97e7*A/s.VRP
    ok = (np.abs(r-1)<0.01).sum()
    print(f"A={A}: n={len(s)} |razon-1|<1%: {ok} ({100*ok/len(s):.2f} %)  mediana={r.median():.4f}")
r = dl*1.97e7*0.5625/s.VRP
bad = s[np.abs(r-1)>=0.01]
print("filas fuera de 1%:", len(bad), " por Satellite:", bad.Satellite.value_counts().to_dict(), " total por Satellite:", s.Satellite.value_counts().to_dict())
print("razon en las fuera, percentiles 5,50,95:", np.percentile(r[np.abs(r-1)>=0.01],[5,50,95]).round(3))
