"""D6: cobertura nocturna del consolidado por mes y sensor, con y sin Tupungatito en el denominador.
Noche y noche_id como en experiments/_s139_audit/bases_mirova_v1/comun.py (hora solar Chile).
Denominador A = dias observados x 11 volcanes (S139). Denominador B = volcan-noches en que el volcan ya existe en la tabla
(cada volcan desde su primera fila). argv: consolidado.csv"""
import sys, pandas as pd
from datetime import timedelta
df = pd.read_csv(sys.argv[1], dtype=str)
df["dt"] = pd.to_datetime(df.Fecha_Satelite_UTC); df["mes"] = df.dt.dt.strftime("%Y-%m")
h = df.dt.dt.hour + df.dt.dt.minute / 60
df["noche"] = (h < 10.7) | (h >= 22.7); df["nid"] = (df.dt + timedelta(hours=1, minutes=18)).dt.date
n = df[df.noche]
vols = sorted(df.Volcan.unique()); first = df.groupby("Volcan").nid.min()
print("volcanes:", len(vols), "primera noche Tupungatito:", first.get("Tupungatito"))
d0, d1 = n.nid.min(), n.nid.max()
for mes in ("2026-01", "2026-02", "2026-03"):
    days = [d for d in pd.date_range(mes + "-01", periods=31).date if d.strftime("%Y-%m") == mes and d0 <= d <= d1]
    for s in ("MODIS", "VIIRS", "VIIRS375"):
        cub = set(map(tuple, n[(n.Sensor == s)][["Volcan", "nid"]].values))
        A = sum((v, d) in cub for v in vols for d in days); denA = len(vols) * len(days)
        v10 = [v for v in vols if v != "Tupungatito"]
        A10 = sum((v, d) in cub for v in v10 for d in days); den10 = len(v10) * len(days)
        posibles = [(v, d) for v in vols for d in days if d >= first[v]]
        B = sum(p in cub for p in posibles)
        print(mes, s, f"11 vol {100*A/denA:.1f}% ({A}/{denA}) | sin Tupungatito {100*A10/den10:.1f}% ({A10}/{den10}) | volcan existente {100*B/len(posibles):.1f}% ({B}/{len(posibles)})")
# control negativo del instrumento: borrar 50 % de enero baja la cobertura
