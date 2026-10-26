# -*- coding: utf-8 -*-
"""V1 (S158) F1-H2 en la unidad del operador (A94): para cada alerta diurna V750 de Chillan perdida, cuantas pasadas
V750 publicadas (>0, predicado del tablero) tiene Chillan en las 24 h previas y en las 24 h siguientes."""
import json, pandas as pd, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = pd.DataFrame(json.load(open("experiments/_s158_audit/v1/pub_v750.json")))
P = P[(P.v == "NevadosDeChillan") & (P.pub > 0)].copy(); P["tt"] = pd.to_datetime(P.t)
for t in ["2026-10-01 18:42", "2026-10-10 18:18", "2026-10-14 18:42", "2026-10-18 19:06"]:
    t0 = pd.Timestamp(t)
    a = P[(P.tt < t0) & (P.tt >= t0 - pd.Timedelta(hours=24))]; b = P[(P.tt > t0) & (P.tt <= t0 + pd.Timedelta(hours=24))]
    print(t, "publicadas V750 24 h antes:", len(a), a.t.tolist(), "| 24 h despues:", len(b), b.t.tolist())
