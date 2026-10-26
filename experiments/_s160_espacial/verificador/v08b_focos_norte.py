# -*- coding: utf-8 -*-
"""V08b: E-08, focos debiles al N de Isluga y Tupungatito (celdas 0,02 grados de 02d), por etiqueta y franja dia/noche
(misma franja que v09), con la Distancia_km de MIROVA en las ALERTA y fechas distintas. Fuente: CSV 02b reproducido."""
import io, sys
from pathlib import Path
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parents[1]
df = pd.read_csv(AUD / "02b_tif_v375_focos.csv")
df["h"] = pd.to_datetime(df.t).dt.hour
df["franja"] = df.h.apply(lambda h: "noche" if (3 <= h < 10 or h >= 22 or h < 3) else "dia")
df["lab"] = df.mir_tipo.fillna("").apply(lambda s: "ALERTA" if s.startswith("ALERTA") else (s or "sin fila"))
for v, (la, lo) in (("Isluga", (-19.10, -68.84)), ("Tupungatito", (-33.34, -69.84))):
    s = df[(df.vol == v) & ((df.lat / 0.02).round() * 0.02 - la).abs().lt(1e-9) & ((df.lon / 0.02).round() * 0.02 - lo).abs().lt(1e-9)]
    print(f"== {v} celda ({la},{lo}): {len(s)} TIF; {s.groupby(['lab','franja']).size().to_dict()}; fechas distintas {s.t.str[:10].nunique()}; "
          f"prominencia p50 {s.res_sigma.median():.1f}; d_centro p50 {s.d_centro.median():.2f} km")
    a = s[s.lab == "ALERTA"]
    if len(a):
        print("   ALERTA: Distancia_km de MIROVA", a.mir_dist.tolist(), "| d(foco, centro TIF)", [round(x, 2) for x in a.d_centro], "| dt min", a.mir_dt_min.tolist())
