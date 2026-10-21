# -*- coding: utf-8 -*-
"""F6 M7: alcance chileno de las filas fuera de la identidad y piso de VRP por Dayflag.
Denominador: filas V750 del OSF v2.5 (2012-2025) de los 11 Tier A (nombres buscados por subcadena)."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = pd.read_pickle(sys.argv[1])
K = 1.97e7 * 0.5625
d["kdl"] = K * (d.Tot_Lmir_hot - d.Tot_Lmir_bk)
d["r"] = d.VRP / d.kdl
d["fuera"] = (d.r - 1).abs() >= 1e-4
print("VRP min por Dayflag (MW):", (d.groupby("Dayflag").VRP.min()/1e6).round(4).to_dict())
pat = "Lascar|L.scar|Lastarria|Isluga|Chill|Llaima|Villarrica|Chait|Planch|Peteroa|Tupungatito|Copahue|Puyehue|Cord"
ch = d[d.Volc_Name.str.contains(pat, case=False, regex=True)]
print("\nfilas V750 Tier A chilenos:", len(ch))
print(ch.groupby("Volc_Name").agg(n=("VRP","size"), fuera=("fuera","sum"), cenit_gt50=("SatZen", lambda s: (s>50).sum()),
      vrp_med_MW=("VRP", lambda s: round(s.median()/1e6,1))).to_string())
print("\nfuera chilenas (todas):")
print(ch[ch.fuera][["timeUTC","Volc_Name","Dayflag","SatZen","Npix","VRP","r","Max_Dist"]].to_string())
print("\nr en fuera por Dayflag:", d[d.fuera].groupby("Dayflag").r.median().round(3).to_dict())
