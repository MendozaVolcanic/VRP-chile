# -*- coding: utf-8 -*-
"""V1 (S158) F1-H5: los 19 publicados V750 en K sin primer pase, contra MIROVA en la misma pasada (|dt| <= 8 min):
alerta (v1/cruce_v750_k.csv), RUTINA (MIROVA miro y no vio, latest_consolidado.csv Sensor VIIRS), o sin fila."""
import pandas as pd, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pd.read_csv("experiments/_s158_audit/v1/h3_caja.csv"); R = R[R.fp == 0].copy()
C = pd.read_csv("experiments/_s158_audit/v1/cruce_v750_k.csv"); C["tt"] = pd.to_datetime(C.t)
T = pd.read_csv("latest_consolidado.csv"); T = T[T.Sensor == "VIIRS"].copy(); T["tt"] = pd.to_datetime(T.Fecha_Satelite_UTC)
alias = {"NevadosDeChillan": "Nevados de Chillan", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
out = []
for _, r in R.iterrows():
    v = alias.get(r.v, r.v); t = pd.Timestamp(r.t)
    a = C[(C.volcan == v) & ((C.tt - t).abs() <= pd.Timedelta(minutes=8))]
    f = T[(T.Volcan == v) & ((T.tt - t).abs() <= pd.Timedelta(minutes=8))]
    out.append(dict(v=r.v, t=r.t, pub=r.pub, mirova="ALERTA %.2f" % a.vrp.max() if len(a) else (",".join(sorted(set(f.Tipo_Registro))) or "sin fila")))
O = pd.DataFrame(out); print(O.to_string(index=False)); print(O.mirova.str.split().str[0].value_counts().to_dict())
