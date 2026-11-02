# -*- coding: utf-8 -*-
"""VPR172 V-3/V-4: en R25 (2025-02-15..12-31), para cada protegida OSF (borrador §4.2), busca el record de K de disco a +-120 s
(mismo bucket) y mira si K la publica con el predicado del tablero (node). Responde: ¿cuanta evidencia P1-OSF hay realmente?
P1: control positivo = n protegidas 317/17/162 (reproducen el borrador). P2: si K no tiene records en 2025, 'sin record' =100% -> SIN DATO."""
import sys, os, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main"
sys.path.insert(0, EXP); sys.path.insert(0, EXP + r"\scripts"); os.chdir(EXP)
import pandas as pd, numpy as np
from datetime import timedelta
import banco_paridad as bp
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
recs = bp.cargar_nuestros(coords, inner, ("2025-02-15","2025-12-31"))
print("records K nocturnos R25:", len(recs), collections.Counter(r["sensor"] for r in recs))
import collections as C
print("K records por mes:", sorted(C.Counter(r["noche"][:7] for r in recs).items()))
w = pd.read_pickle(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\osf_w.pkl")
pr = w[(w["class"]==1)&(w.VRP>=1e6)&(w.d_vent<=w.inner)].copy()
nm = {"Chaitén":"Chaiten","Chillán, Nevados de":"NevadosDeChillan","Copahue":"Copahue","Isluga":"Isluga","Lastarria":"Lastarria","Llaima":"Llaima","Láscar":"Lascar","Planchón-Peteroa":"PlanchonPeteroa","Puyehue-Cordón Caulle":"PuyehueCordonCaulle","Villarrica":"Villarrica"}
bk = {375:"VIIRS375",750:"VIIRS750",1000:"MODIS"}
idx = C.defaultdict(list)
for r in recs: idx[(r["vol"], r["b"])].append(r)
out=[]
for row in pr.itertuples():
    v = nm[row.Volc_Name]; b = bk[row.Resolution]; t = row.t.to_pydatetime().replace(tzinfo=recs[0]["dt"].tzinfo)
    m = [r for r in idx[(v,b)] if abs((r["dt"]-t).total_seconds())<=120]
    out.append(dict(vol=v,b=b,sat=int(row.Satellite),t=str(t),vrp=row.VRP/1e6,n_rec=len(m),
                    pub=any(r["pub"] for r in m), dts=[int((r["dt"]-t).total_seconds()) for r in m], sensor=[r["sensor"] for r in m]))
d = pd.DataFrame(out)
print(d.groupby("b").agg(n=("vol","size"), con_record=("n_rec", lambda s:(s>0).sum()), K_publica=("pub","sum"), dos_records=("n_rec", lambda s:(s>1).sum())))
print("sin record por sat y bucket:"); print(d[d.n_rec==0].groupby(["b","sat"]).size())
print("K no publica pero hay record, por bucket y volcan:"); print(d[(d.n_rec>0)&(~d.pub)].groupby(["b","vol"]).size())
print("dt (s) de los pares: distribucion"); allx=[x for l in d.dts for x in l]; print(pd.Series(allx).describe())
print("sensor de los records pareados:", C.Counter(s for l in d.sensor for s in l))
d.to_csv(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\r25_k_pareo.csv", index=False)
# negativos: cuantas pasadas K de 2025 hay por bucket, y K publica cuantas (para dimensionar P2-informa)
print("K 2025 pasadas por bucket:", C.Counter(r["b"] for r in recs), "publica:", C.Counter(r["b"] for r in recs if r["pub"]))
