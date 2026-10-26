# -*- coding: utf-8 -*-
"""V09 (verificador S160 espacial): 02b no separa TIF diurnos de nocturnos. Aqui se estratifica el CSV 02b (reproducido
byte a byte) por hora de adquisicion: noche = 03:00-09:59 UTC o 22:00-02:59 UTC (Chile, sol bajo el horizonte en las
pasadas VIIRS nocturnas de ~05-07 UTC y en las de ~23-03 UTC del invierno); dia = 10:00-21:59 UTC. Se recalcula foco a vent
(geodesica WGS84) por etiqueta y franja, y la composicion dia/noche de cada etiqueta y de la celda de la fuente E de PCC.
P1: si la franja no importara, las cifras de dia y noche coincidirian; P2: n por celda; vacio = SIN DATO.
"""
import io, sys
from pathlib import Path
import pandas as pd
from pyproj import Geod
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parents[1]
G = Geod(ellps="WGS84")
VENT = {"PuyehueCordonCaulle": (-40.525499, -72.146137), "Tupungatito": (-33.389044, -69.826374), "Isluga": (-19.15, -68.83),
        "Lascar": (-23.36293, -67.731416)}
df = pd.read_csv(AUD / "02b_tif_v375_focos.csv")
df = df[df.vol.isin(list(VENT))].copy()
df["h"] = pd.to_datetime(df.t).dt.hour
df["franja"] = df.h.apply(lambda h: "noche" if (3 <= h < 10 or h >= 22 or h < 3) else "dia")
df["d_vent"] = [G.inv(VENT[r.vol][1], VENT[r.vol][0], r.lon, r.lat)[2] / 1000 for r in df.itertuples()]
df["lab"] = df.mir_tipo.fillna("").apply(lambda s: "ALERTA" if s.startswith("ALERTA") else (s or "sin fila"))
for v in VENT:
    dv = df[df.vol == v]
    print(f"\n== {v}: TIF {len(dv)}; por etiqueta y franja: {dv.groupby(['lab','franja']).size().to_dict()}")
    for lab in ("ALERTA", "RUTINA"):
        for fr in ("noche", "dia"):
            s = dv[(dv.lab == lab) & (dv.franja == fr)]
            if len(s) == 0:
                print(f"   {lab:7s} {fr:5s}: SIN DATO")
                continue
            print(f"   {lab:7s} {fr:5s}: n={len(s):3d} foco a vent p50 {s.d_vent.median():5.2f} km, <=1 km {100*(s.d_vent<=1).mean():3.0f} %, prominencia p50 {s.res_sigma.median():.1f}")
pcc = df[(df.vol == "PuyehueCordonCaulle") & ((df.lat / 0.02).round() * 0.02 == -40.52) & (((df.lon / 0.02).round() * 0.02 + 72.02).abs() < 1e-9)]
print(f"\nfuente E de PCC (celda -40,52/-72,02): {pcc.groupby(['lab','franja']).size().to_dict()}")
print("TIF de PCC por mes y franja:", df[df.vol == "PuyehueCordonCaulle"].groupby([df.t.str[:7], "franja"]).size().to_dict())
