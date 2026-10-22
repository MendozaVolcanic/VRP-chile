# -*- coding: utf-8 -*-
"""V1 (S158) verificacion de F1-H3: publicados VIIRS 750 en K con todos sus pixeles fuera de una caja 7x7 de 750 m
centrada en el centro de grilla de MIROVA (mirova_center_lat/lon de volcanoes.yaml), y donde publica MIROVA.

Publicado = predicado del tablero ejecutado con node (f1/predicado_tablero.js, extrae el JS de frontend/index.html),
salida en v1/pub_v750.json. Ventana: datetime_utc >= 2026-09-18 hasta el ultimo record (2026-10-21 06:48).
Pixeles: anomaly_pixels del record (top-100 por VRP; si n_anomalous_pixels > 100 la cuenta es parcial, se reporta).
Caja: |dx| <= 3,5 celdas y |dy| <= 3,5 celdas (2,625 km) en proyeccion local equirectangular desde el centro.
Pregunta 1: si todos los publicados estuvieran fuera, se veria (se cuenta por volcan). Pregunta 2: si la geometria
estuviera rota (centro equivocado) todos caerian fuera, incluidos volcanes de cumbre puntual; el control positivo es
que Lascar o Villarrica caigan DENTRO.
"""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd, yaml
here = os.path.dirname(os.path.abspath(__file__))
pub = pd.DataFrame(json.load(open(os.path.join(here, "pub_v750.json"))))
pub = pub[(pub.pub > 0) & (pub.t >= "2026-09-18")]
vy = {v["name"]: v for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
res = []
for vol, g in pub.groupby("v"):
    d = json.load(open(f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    idx = {(r["datetime_utc"], r["sensor"]): r for r in d["records"]}
    c = vy[vol]
    la0 = c.get("mirova_center_lat") or c["lat"]; lo0 = c.get("mirova_center_lon") or c["lon"]
    for _, p in g.iterrows():
        r = idx[(p.t, p.s)]
        px = r.get("anomaly_pixels") or []
        dx = np.array([(q["lon"] - lo0) * 111.32 * np.cos(np.radians(la0)) for q in px])
        dy = np.array([(q["lat"] - la0) * 111.32 for q in px])
        inb = (np.abs(dx) <= 2.625) & (np.abs(dy) <= 2.625)
        pc = r.get("primary_cluster") or {}
        res.append(dict(v=vol, t=p.t, s=p.s, pub=p.pub, npx=len(px), ntot=r.get("n_anomalous_pixels"), n_en_caja=int(inb.sum()),
                        dmin_centro=float(np.hypot(dx, dy).min()) if len(px) else np.nan, pc_dist=pc.get("centroid_dist_km"),
                        fp=r.get("diag_n_first_pass_pixels"), sp=r.get("diag_n_second_pass_recapture")))
R = pd.DataFrame(res)
R.to_csv(os.path.join(here, "h3_caja.csv"), index=False)
print("publicados V750 en ventana:", len(R))
print(R.groupby("v").agg(n=("t", "size"), fuera=("n_en_caja", lambda x: int((x == 0).sum()))).to_string())
print("con todos los pixeles fuera de la caja:", int((R.n_en_caja == 0).sum()), " registros truncados a 100 entre ellos:",
      int(((R.n_en_caja == 0) & (R.ntot > R.npx)).sum()))
print(R[R.n_en_caja == 0][["v", "t", "s", "pub", "ntot", "dmin_centro", "pc_dist", "fp", "sp"]].to_string(index=False))
# donde publica MIROVA PCC (VIIRS 750, tabla): distancias
cons = pd.read_csv("latest_consolidado.csv")
m = cons[(cons.Volcan == "Puyehue-Cordon Caulle") & (cons.Sensor == "VIIRS") & (cons.Tipo_Registro == "ALERTA_TERMICA")]
print("\nMIROVA PCC VIIRS 750 ALERTA_TERMICA, toda la tabla:", len(m), " Distancia_km cuantiles:",
      m.Distancia_km.quantile([0, .25, .5, .75, 1]).round(2).tolist())
mk = m[m.Fecha_Satelite_UTC >= "2026-09-18"]
print("idem en K:", len(mk), sorted(mk.Distancia_km.round(2).tolist()))
print("alertas MIROVA PCC V750 a <= 3,7 km (diagonal de la caja) en toda la tabla:", int((m.Distancia_km <= 3.71).sum()))
