"""Afirmación 6, contexto: ¿MIROVA publica en su propio archivo (OSF v2.5, 2025) pasadas VIIRS 750 DIURNAS
(Dayflag != 0) para los volcanes chilenos Tier A? Si lo hace, el rechazo diurno es decisión nuestra, no de
MIROVA (coincide con el .m: de día cambia umbrales, no rechaza, salvo sun-glint < 12 grados).
Archivo: data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv (fuera del worktree, sólo lectura). Columnas
Dayflag y Resolution leídas del header. Pregunta 1: si MIROVA no procesara de día, Dayflag=1 daría 0 filas en
todo el archivo (control: se imprime el total global por Dayflag). Pregunta 2: si el archivo no cargara, excepción."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(p, usecols=["timeUTC", "Dayflag", "Satellite", "Resolution", "VRP", "Volc_Name", "SatZen", "class"])
print("filas", len(df), "| Resolution:", df.Resolution.value_counts().to_dict(), "| Dayflag:", df.Dayflag.value_counts().to_dict(), "| Satellite:", df.Satellite.value_counts().to_dict())
print("fechas:", df.timeUTC.min(), "..", df.timeUTC.max())
chile = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "Planchon", "Chillan", "Llaima", "Villarrica", "Copahue", "Puyehue", "Chaiten"]
m = df.Volc_Name.fillna("").str.contains("|".join(chile), case=False, regex=True)
d = df[m]
print("nombres chilenos encontrados:", d.Volc_Name.value_counts().to_dict())
t = d.groupby(["Resolution", "Dayflag"]).size().unstack(fill_value=0)
print("\nfilas por Resolution x Dayflag (volcanes chilenos):\n", t)
v750 = d[d.Resolution == 750]
print("\nVIIRS 750 chilenos: n =", len(v750), "| diurnas (Dayflag!=0):", int((v750.Dayflag != 0).sum()),
      "| diurnas con VRP >= 1 MW:", int(((v750.Dayflag != 0) & (v750.VRP >= 1e6)).sum()), "(VRP en W: ", v750.VRP.describe()[["min", "50%", "max"]].to_dict(), ")")
print("VIIRS 750 chilenos diurnos por volcán:", v750[v750.Dayflag != 0].Volc_Name.value_counts().to_dict())
print("VIIRS 750 chilenos, mediana VRP (MW) noche vs dia:", (v750[v750.Dayflag == 0].VRP / 1e6).median(), (v750[v750.Dayflag != 0].VRP / 1e6).median())
