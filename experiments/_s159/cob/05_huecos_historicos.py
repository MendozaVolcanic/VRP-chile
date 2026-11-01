# -*- coding: utf-8 -*-
"""COB 05 (S159). Huecos historicos de la serie propia: records por dia UTC y plataforma, 2025-02-15 .. 2026-10-21,
11 Tier A, desde el REMOTO (_remoto/, bajado 2026-10-21 ~18 UTC).
Pregunta 1: si faltara un dia completo de una plataforma, la tabla lo da como 0 (control positivo: 13-oct y 20-oct-2026,
conocidos por 03). Pregunta 2: si el JSON no cargara, el assert aborta. Umbral: dia/plataforma con 0 records, y dia con
total bajo 0,5 x mediana movil de 29 dias. Se informa el denominador (dias de la ventana)."""
import json, sys, io
from pathlib import Path
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob")
VOLS = ["Lascar","Chaiten","PuyehueCordonCaulle","Lastarria","Villarrica","NevadosDeChillan","Isluga","Copahue","PlanchonPeteroa","Llaima","Tupungatito"]
rows=[]
for v in VOLS:
    for r in json.load(open(HERE/"_remoto"/f"{v}.json",encoding="utf-8"))["records"]:
        rows.append((v,pd.Timestamp(r["datetime_utc"]),r["sensor"]))
df=pd.DataFrame(rows,columns=["vol","t","sensor"]); assert len(df)>0
df["plat"]=df.sensor.str.replace("_750","",regex=False)
df["dia"]=df.t.dt.normalize()
ini=pd.Timestamp("2025-02-15"); fin=pd.Timestamp("2026-10-20")
df=df[(df.dia>=ini)&(df.dia<=fin)]
print("records:",len(df),"| dias en la ventana:",(fin-ini).days+1,"| volcanes:",df.vol.nunique())
# Tupungatito empieza despues; denominador por volcan
print("primer record por volcan:",df.groupby("vol").t.min().dt.strftime("%Y-%m-%d").to_dict())
d=df[df.sensor.isin(["VIIRS_SNPP","VIIRS_NOAA20","VIIRS_NOAA21","MODIS_AQUA","MODIS_TERRA"])]
tab=d.groupby(["dia","plat"]).size().unstack(fill_value=0).reindex(pd.date_range(ini,fin),fill_value=0)
# NOAA-21 solo existe en la serie desde que se agrego; mirar primer dia con records
print("primer dia con records por plataforma:",{c:str(tab.index[tab[c]>0][0].date()) for c in tab})
for c in tab:
    prim=tab.index[tab[c]>0][0]
    z=tab.loc[prim:,c]; z=z[z==0]
    print(f"\n{c}: dias con 0 records desde su primer dia ({prim.date()}): {len(z)} de {(fin-prim).days+1}")
    # agrupar en rachas
    ds=list(z.index); rachas=[]
    for x in ds:
        if rachas and (x-rachas[-1][1]).days==1: rachas[-1][1]=x
        else: rachas.append([x,x])
    print("  rachas:", [f"{a.date()}" + (f"..{b.date()}" if b!=a else "") for a,b in rachas])
tot=tab.sum(axis=1)
mm=tot.rolling(29,center=True,min_periods=15).median()
bajo=tot[tot<0.5*mm]
print("\ndias con total < 0,5 x mediana movil de 29 d:",len(bajo))
print([f"{x.date()}:{int(v)}" for x,v in bajo.items()])
