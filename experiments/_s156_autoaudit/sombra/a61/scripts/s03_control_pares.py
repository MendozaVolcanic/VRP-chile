# -*- coding: utf-8 -*-
"""Control (4): en pasadas de PCC donde MIROVA alerto (tabla CONS, sin RUTINA) y nosotros tenemos cumulo en el
mismo sensor y la misma pasada (+-3 min), relacion entre nuestra posicion y su Distancia_km.
Uso: python -I s03_control_pares.py <worktree> <consolidado.csv>"""
import csv, json, math, sys
from datetime import datetime
from pathlib import Path
import numpy as np
from pyproj import Transformer

WT = Path(sys.argv[1]); CSV = Path(sys.argv[2]); OUT = Path(__file__).resolve().parents[1] / "salidas"
utm = Transformer.from_crs("EPSG:4326", "EPSG:32718", always_xy=True)
def xy(lat, lon):
    x, y = utm.transform(lon, lat); return x / 1000.0, y / 1000.0
MC = (-40.5903, -72.1187); VENT = (-40.525499, -72.146137)
cx, cy = xy(*MC)
CEL = {"750": 0.75, "375": 0.375}

al = []
for r in csv.DictReader(open(CSV, encoding="utf-8")):
    if "Puyehue" not in r["Volcan"] or r["Tipo_Registro"] == "RUTINA":
        continue
    b = "750" if r["Sensor"] == "VIIRS" else ("375" if r["Sensor"] == "VIIRS375" else None)
    if b is None:
        continue
    al.append((datetime.strptime(r["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S"), b, float(r["VRP_MW"]), float(r["Distancia_km"]), r["Tipo_Registro"]))
print(f"alertas PCC VIIRS en la tabla (sin RUTINA): {len(al)}; ventana {min(a[0] for a in al)} a {max(a[0] for a in al)}")

def banda(s):
    return "750" if s.endswith("_750") else "375"
res = {}
for perfil in ["mirova_equivalent", "experimental_v2"]:
    recs = json.load(open(WT / f"data/{perfil}/PuyehueCordonCaulle.json", encoding="utf-8"))["records"]
    idx = {}
    for r in recs:
        if not r["sensor"].startswith("VIIRS"):
            continue
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        idx.setdefault(banda(r["sensor"]), []).append((t, r))
    filas = []
    for t, b, vrp, dm, tipo in al:
        cand = [r for tt, r in idx.get(b, []) if abs((tt - t).total_seconds()) <= 180]
        if not cand:
            continue
        r = cand[0]
        pc = r.get("primary_cluster")
        aps = [p for p in (r.get("anomaly_pixels") or []) if p.get("vrp_mw") is not None]
        f = {"t": t.isoformat(sep=" "), "banda": b, "mirova_vrp": vrp, "mirova_dist": dm, "tiene_pc": pc is not None,
             "vrp_pub": (pc or {}).get("vrp_mw")}
        if pc:
            for nom, (la, lo) in {"pc": (pc["centroid_lat"], pc["centroid_lon"]),
                                   "pxmax": ((max(aps, key=lambda p: p["vrp_mw"])["lat"], max(aps, key=lambda p: p["vrp_mw"])["lon"]) if aps else (None, None))}.items():
                if la is None:
                    continue
                x, y = xy(la, lo)
                de, dn = x - cx, y - cy
                c = CEL[b]
                dq = math.hypot(round(de / c), round(dn / c)) * c
                vx, vy = xy(*VENT)
                f[f"{nom}_d_centro"] = round(math.hypot(de, dn), 3)
                f[f"{nom}_d_cuant"] = round(dq, 3)
                f[f"{nom}_d_vent"] = round(math.hypot(x - vx, y - vy), 3)
                f[f"{nom}_rumbo_desde_centro"] = round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1)
        filas.append(f)
    con = [f for f in filas if f["tiene_pc"]]
    print(f"\n== perfil {perfil}: pares alerta MIROVA + record nuestro misma pasada: {len(filas)}; con cumulo publicado {len(con)}")
    for b in ["750", "375"]:
        cb = [f for f in con if f["banda"] == b]
        if not cb:
            continue
        dif = np.array([f["pc_d_centro"] - f["mirova_dist"] for f in cb])
        difq = np.array([f["pc_d_cuant"] - f["mirova_dist"] for f in cb])
        dv = np.array([f["pc_d_vent"] for f in cb])
        rb = np.array([f["pc_rumbo_desde_centro"] for f in cb])
        print(f"   V{b}: n={len(cb)} | nuestro centroide: dist al centro de MIROVA menos Distancia_km: mediana {np.median(dif):+.2f} km, "
              f"|dif| p50 {np.median(abs(dif)):.2f} p90 {np.percentile(abs(dif),90):.2f} | cuantizada: |dif| <=0.01 en {int((abs(difq)<=0.011).sum())}, "
              f"<= 1 celda en {int((abs(difq)<=CEL[b]+0.01).sum())} | dist al vent: mediana {np.median(dv):.2f} p90 {np.percentile(dv,90):.2f} km"
              f" | rumbo desde centro: mediana {np.median(rb):.0f} grados (p10 {np.percentile(rb,10):.0f}, p90 {np.percentile(rb,90):.0f})")
        dm = np.array([f["mirova_dist"] for f in cb])
        print(f"        Distancia_km de MIROVA en esos pares: mediana {np.median(dm):.2f}, p10 {np.percentile(dm,10):.2f}, p90 {np.percentile(dm,90):.2f}")
    res[perfil] = filas
(OUT / "s03_control_pares.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
