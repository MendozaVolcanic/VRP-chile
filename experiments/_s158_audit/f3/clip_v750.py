# -*- coding: utf-8 -*-
"""F3: detalle de las alertas V750 de MIROVA (tabla, 2026-03-01 a 2026-10-20, noche) donde nuestro cúmulo publica 0 MW.
Pregunta: ¿el 0 viene del recorte ΔL >= 0 con el fondo de anillo (L_hot del píxel alertado < L_bg del anillo) o de la
clasificación (far / fuera del inner)? Instrumento: se imprime, por pasada, la BT M13 del píxel alertado más caliente,
la BT del fondo (t_bg_k) y su diferencia; si el recorte fuera la causa, la diferencia es <= 0 en esas pasadas y > 0 en
las publicadas (control positivo: las publicadas del mismo volcán).
Uso: python -B clip_v750.py <raiz> scraper2026_filas.csv
"""
import json, os, sys
from datetime import datetime, timedelta
import pandas as pd
ROOT, F = sys.argv[1], sys.argv[2]
D = pd.read_csv(F)
D = D[(D.b == "V750") & D.vol.isin(["Tupungatito", "PlanchonPeteroa", "Isluga", "Villarrica", "PuyehueCordonCaulle"])]
print(D.groupby("vol").agg(n=("M", "size"), no_pub=("pub", lambda x: int((x <= 0).sum()))).to_string())
for vol in ["Tupungatito", "PlanchonPeteroa", "Isluga"]:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"), encoding="utf-8"))
    recs = [r for r in d["records"] if "750" in str(r.get("sensor"))]
    print(f"\n{vol}: pasadas V750 nocturnas desde 2026-03-01 con >=1 alertado, por resultado de magnitud del cúmulo")
    rows = []
    for r in recs:
        t = str(r["datetime_utc"])
        if t < "2026-03-01" or not (3 <= int(t[11:13]) <= 9) or not (r.get("n_anomalous_pixels") or 0):
            continue
        px = r.get("anomaly_pixels") or []
        if not px:
            continue
        pc = r.get("primary_cluster") or {}
        bmax = max(p["bt_k"] for p in px)
        rows.append({"t": t, "dclass": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"),
                     "bt_max": bmax, "t_bg": r.get("t_bg_k"), "dT": bmax - (r.get("t_bg_k") or float("nan")),
                     "n_clip": sum(1 for p in px if p["vrp_mw"] <= 0), "n": len(px), "zen": r.get("sensor_zenith_deg")})
    R = pd.DataFrame(rows)
    R["cero"] = R.pc_vrp.fillna(0) <= 0
    print(R.groupby("cero").agg(n=("t", "size"), dT_med=("dT", "median"), dT_max=("dT", "max"), dT_min=("dT", "min"),
                                todos_recortados=("n_clip", lambda x: int((x == R.loc[x.index, "n"]).sum()))).round(2).to_string())
    al = D[(D.vol == vol) & (D.pub <= 0)]
    print("  ejemplos de alertas de MIROVA con nuestra magnitud 0 (para reproducir):")
    for _, a in al.head(4).iterrows():
        print(f"   M={a.M} MW zen={a.zen} dclass={a.dclass} clip={a.clip} tbg={a.tbg} tmax={a.tmax}")
    print(R[R.cero].head(5).to_string(index=False))
