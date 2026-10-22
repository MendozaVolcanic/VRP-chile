# -*- coding: utf-8 -*-
"""V1 (S158) consecuencia real de F1-H1: records VIIRS 750 en K (>= 2026-09-18) con pixeles detectados pero VRP
publicado 0 (predicado del tablero, v1/pub_v750.json), y cuantos tienen todos sus pixeles con bt <= t_bg (el recorte
los deja en 0). Cruce con alertas MIROVA V750 (v1/cruce_v750_k.csv, |dt| <= 8 min).
Pregunta 2: si el instrumento estuviera muerto daria 0 records con pixeles; control: se imprime el total con pixeles."""
import json, pandas as pd, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = pd.DataFrame(json.load(open("experiments/_s158_audit/v1/pub_v750.json")))
P = P[P.t >= "2026-09-18"]
C = pd.read_csv("experiments/_s158_audit/v1/cruce_v750_k.csv")
rows = []
for vol, g in P.groupby("v"):
    d = json.load(open(f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    idx = {(r["datetime_utc"], r["sensor"]): r for r in d["records"]}
    for _, p in g.iterrows():
        r = idx[(p.t, p.s)]
        n = r.get("n_anomalous_pixels") or 0
        if n == 0:
            continue
        px = r.get("anomaly_pixels") or []
        pc = r.get("primary_cluster") or {}
        rows.append(dict(v=vol, t=p.t, s=p.s, pub=p.pub, n=n, dclass=r.get("distance_class"), pc_vrp=pc.get("vrp_mw"),
                         pc_dist=pc.get("centroid_dist_km"),
                         todos_bajo_tbg=all(q["bt_k"] <= r["t_bg_k"] for q in px) if px else None))
X = pd.DataFrame(rows)
print("records V750 en K con pixeles:", len(X), " publicados >0:", int((X.pub > 0).sum()))
z = X[X.pub == 0]
print("con pixeles y publicado 0:", len(z), " de ellos summit:", int((z.dclass == "summit").sum()),
      " summit con pc.vrp == 0:", int(((z.dclass == "summit") & (z.pc_vrp == 0)).sum()),
      " summit con todos los pixeles bt <= t_bg:", int(((z.dclass == "summit") & (z.todos_bajo_tbg == True)).sum()))
zs = z[(z.dclass == "summit") & (z.pc_vrp == 0)].copy()
alias = {"NevadosDeChillan": "Nevados de Chillan", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
C["tt"] = pd.to_datetime(C.t)
m = []
for _, r in zs.iterrows():
    cv = C[(C.volcan == alias.get(r.v, r.v)) & ((C.tt - pd.Timestamp(r.t)).abs() <= pd.Timedelta(minutes=8))]
    m.append(cv.vrp.max() if len(cv) else None)
zs["mirova_vrp"] = m
print(zs.groupby("v").size().to_dict())
print("de esos, con alerta MIROVA V750 en la misma pasada:", int(zs.mirova_vrp.notna().sum()))
print(zs[zs.mirova_vrp.notna()].to_string(index=False))
