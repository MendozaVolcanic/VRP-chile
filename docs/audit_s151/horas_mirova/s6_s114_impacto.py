"""s6: cuantas filas VIIRS375 trataria como nocturnas el is_daytime (hora local 10-15) de
experiments/_s114_audit/viirs375_deepdive.py siendo diurnas por hora UTC (>=11h), hasta el 2026-06-20."""
import sys, pandas as pd
for p in sys.argv[1:]:
    d = pd.read_csv(p); u = pd.to_datetime(d.Fecha_Satelite_UTC); h = pd.to_datetime(d.Fecha_Captura_Chile).dt.hour
    m = (d.Sensor == "VIIRS375") & (u < "2026-06-20")
    mal = m & (u.dt.hour >= 11) & ((h > 15) | (h < 10))
    print(p, "VIIRS375 hasta 2026-06-20:", int(m.sum()), "| diurnas tratadas como nocturnas:", int(mal.sum()),
          "| de ellas ALERTA:", int((mal & d.Tipo_Registro.str.startswith("ALERTA")).sum()),
          "| por mes:", d[mal].Fecha_Satelite_UTC.str[:7].value_counts().sort_index().to_dict())
