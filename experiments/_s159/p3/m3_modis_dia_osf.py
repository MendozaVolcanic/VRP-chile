# M3. ¿MIROVA publica MODIS diurno? Conteo en el OSF v2.5 (filas Dayflag=1, Resolution=1000).
# Pregunta 1: si MIROVA no publicara MODIS de día, el conteo daría 0; si sí, >0. Lo ve.
# Pregunta 2: control: el mismo conteo para VIIRS 750 de día debe dar >0 (R2-10 ya lo vio en NRT).
# Límite: el OSF trae sólo filas con VRP sobre el umbral por sensor y clase (A105); un 0 en un
# volcán no prueba que MIROVA calle, sólo que no hubo fila sobre el umbral.
import sys, io, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(F)
d["t"] = pd.to_datetime(d["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
day = d[d.Dayflag == 1]
print("ventana", d.t.min(), "->", d.t.max())
print(day.groupby("Resolution").size().rename("filas_dia"))
print("VRP mínimo de día por sensor (W):", day.groupby("Resolution").VRP.min().to_dict())
chile = d[(d.Volc_LAT < -17) & (d.Volc_LAT > -56) & (d.Volc_LON > -76) & (d.Volc_LON < -66)]
cd = chile[chile.Dayflag == 1]
print("\nChile (caja lat -17 a -56, lon -76 a -66), filas de día por volcán y sensor:")
print(cd.groupby(["Volc_Name", "Resolution"]).size().to_string() if len(cd) else "  0 filas")
print("Chile, MODIS diurno por año:", cd[cd.Resolution == 1000].t.dt.year.value_counts().sort_index().to_dict())
