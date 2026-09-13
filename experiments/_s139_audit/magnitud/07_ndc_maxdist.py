"""S139 magnitud, paso 7: donde esta lo que MIROVA suma en NdC feb-mar 2025 (LAT/LON y Max_Dist del OSF)
y, para todos los pares V375, si R depende de Max_Dist (MIROVA suma pixeles lejanos dentro de su ROI).
Instrumento: si Max_Dist no informara nada, R no variaria entre bins; control: NdC debe caer en el bin lejano."""
import pathlib, numpy as np, pandas as pd, math
R = pathlib.Path(__file__).resolve().parents[3]
o = pd.read_csv(R / 'data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv')
n = o[(o.Volc_Name == 'Chillán, Nevados de') & o.timeUTC.str.contains('/0[23]/2025') & (o.Dayflag == 0) & (o['class'] == 1)]
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))
n = n.assign(dist_centroide_km=[hav(a, b, c, d) for a, b, c, d in zip(n.LAT, n.LON, n.Volc_LAT, n.Volc_LON)])
print(n[['timeUTC', 'Resolution', 'Npix', 'VRP', 'LAT', 'LON', 'Max_Dist', 'dist_centroide_km']].head(20).to_string())
print('\nOSF Max_Dist unidades: cuantiles globales', o.Max_Dist.quantile([.5, .9, .99]).to_dict())
d = pd.read_csv(R / 'experiments/_s139_audit/magnitud/02_pares.csv'); d = d[d.res == 375]
