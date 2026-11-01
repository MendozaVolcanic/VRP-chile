# -*- coding: utf-8 -*-
"""Control con GeoTIFF: en alertas de MIROVA de PCC (VIIRS 750 y 375, tabla CONS) con TIF de la misma pasada
(adquisicion +-120 s, md5 no ambiguo, antes del congelamiento del 2026-09-22), donde esta el foco de MIROVA y
donde estaba nuestro cumulo. Reusa comun_tif.py del estudio 1.4 (PR #809). Los TIF se bajan por raw a
bajados/tif (nunca clone/pull del archivo de TIF).
Uso: python -I s04_tif_control.py <worktree> <consolidado.csv>"""
import csv, json, math, os, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

WT = Path(sys.argv[1]); CSV = Path(sys.argv[2])
BASE = Path(__file__).resolve().parents[1]
os.environ["VRP_TIF_CACHE"] = str(BASE / "bajados" / "tif_cache")
sys.path.insert(0, str(WT / "experiments" / "_s151_seleccion_mirova"))
import comun_tif as T  # noqa

VENT = (-40.525499, -72.146137); MC = (-40.5903, -72.1187)
ix = T.indice()
ix = ix[ix.vol == "PuyehueCordonCaulle"]
al = []
for r in csv.DictReader(open(CSV, encoding="utf-8")):
    if "Puyehue" not in r["Volcan"] or r["Tipo_Registro"] == "RUTINA":
        continue
    s = {"VIIRS": "VIIRS750", "VIIRS375": "VIIRS375"}.get(r["Sensor"])
    if s:
        al.append((pd.Timestamp(r["Fecha_Satelite_UTC"], tz="UTC"), s, float(r["VRP_MW"]), float(r["Distancia_km"])))

recs = {}
for perfil in ["mirova_equivalent", "experimental_v2"]:
    for r in json.load(open(WT / f"data/{perfil}/PuyehueCordonCaulle.json", encoding="utf-8"))["records"]:
        if r["sensor"].startswith("VIIRS"):
            b = "VIIRS750" if r["sensor"].endswith("_750") else "VIIRS375"
            recs.setdefault((perfil, b), []).append((pd.Timestamp(r["datetime_utc"], tz="UTC"), r))

def nuestro(perfil, s, t):
    c = [r for tt, r in recs.get((perfil, s), []) if abs((tt - t).total_seconds()) <= 180]
    return c[0] if c else None

filas = []
for t, s, vrp, dm in sorted(al):
    fila, motivo = T.tif_de_pasada(ix[ix.sensor == s], t)
    if fila is None:
        continue
    if not T.bajar_tif(fila):
        continue
    R = T.leer(T.ruta_tif(fila), s)
    if R is None:
        continue
    dc = T.dist_desde(R, R["clat"], R["clon"])
    anillo = np.abs(dc - dm) <= T.TOL_ANILLO_KM[s]
    f_an = T.foco_en(R, anillo)
    f_gl = T.foco_en(R, np.ones_like(anillo, bool))
    dvent = T.dist_desde(R, *VENT)
    f_vent = T.foco_en(R, dvent <= 1.5)
    out = {"t": str(t), "sensor": s, "mirova_vrp": vrp, "mirova_dist": dm, "crs": R["crs"], "motivo_tif": motivo,
           "centro_raster": [round(R["clat"], 5), round(R["clon"], 5)],
           "centro_raster_a_mirova_center_km": round(float(T.dist_km(R["clat"], R["clon"], *MC)), 3),
           "centro_raster_a_vent_km": round(float(T.dist_km(R["clat"], R["clon"], *VENT)), 3)}
    if f_an:
        z, r_, c_ = f_an
        la, lo = float(R["lat"][r_, c_]), float(R["lon"][r_, c_])
        x, y = T.km_xy(la, lo, R["clat"], R["clon"])
        out.update({"foco_anillo_z": round(z, 1), "foco_anillo": [round(la, 5), round(lo, 5)],
                    "foco_anillo_d_vent": round(float(T.dist_km(la, lo, *VENT)), 3),
                    "foco_anillo_d_centro": round(float(T.dist_km(la, lo, R["clat"], R["clon"])), 3),
                    "foco_anillo_rumbo": round((math.degrees(math.atan2(float(x), float(y))) + 360) % 360, 1)})
    if f_gl:
        z, r_, c_ = f_gl
        la, lo = float(R["lat"][r_, c_]), float(R["lon"][r_, c_])
        out.update({"foco_global_z": round(z, 1), "foco_global_d_vent": round(float(T.dist_km(la, lo, *VENT)), 3)})
    if f_vent:
        out["z_max_a_1_5km_del_vent"] = round(f_vent[0], 1)
    # nulo: el mismo disco de 1,5 km girado alrededor del centro del raster (11 angulos)
    nul = []
    for ang in range(30, 360, 30):
        la, lo = T.rotar(*VENT, R["clat"], R["clon"], ang)
        f = T.foco_en(R, T.dist_desde(R, la, lo) <= 1.5)
        if f:
            nul.append(f[0])
    out["z_girado_mediana"] = round(float(np.median(nul)), 1) if nul else None
    out["z_girado_max"] = round(float(np.max(nul)), 1) if nul else None
    for perfil in ["mirova_equivalent", "experimental_v2"]:
        r = nuestro(perfil, s, t)
        if r and r.get("primary_cluster") and "foco_anillo" in out:
            pc = r["primary_cluster"]
            out[f"{perfil}_pc_d_foco_mirova_km"] = round(float(T.dist_km(pc["centroid_lat"], pc["centroid_lon"], *out["foco_anillo"])), 3)
            out[f"{perfil}_pc_vrp"] = pc["vrp_mw"]
    filas.append(out)
    print(json.dumps(out, ensure_ascii=False))

df = pd.DataFrame(filas)
(BASE / "salidas" / "s04_tif_control.json").write_text(json.dumps(filas, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nalertas con TIF legible de la misma pasada: {len(df)} (V750 {int((df.sensor=='VIIRS750').sum())}, V375 {int((df.sensor=='VIIRS375').sum())})")
for s in ["VIIRS750", "VIIRS375"]:
    d = df[df.sensor == s]
    if d.empty:
        continue
    print(f"== {s}: centro del raster a mirova_center: mediana {d.centro_raster_a_mirova_center_km.median():.3f} km (max {d.centro_raster_a_mirova_center_km.max():.3f})")
    print(f"   foco en el anillo de la Distancia_km: z mediana {d.foco_anillo_z.median():.1f}; a <= 1,5 km del vent en {int((d.foco_anillo_d_vent<=1.5).sum())} de {len(d)}; "
          f"d_vent mediana {d.foco_anillo_d_vent.median():.2f} km; rumbo desde el centro mediana {d.foco_anillo_rumbo.median():.0f} grados")
    print(f"   z maximo a <= 1,5 km del vent: mediana {d.z_max_a_1_5km_del_vent.median():.1f}; nulo girado: mediana de medianas {d.z_girado_mediana.median():.1f}, mediana de maximos {d.z_girado_max.median():.1f}")
    for p in ["mirova_equivalent", "experimental_v2"]:
        col = f"{p}_pc_d_foco_mirova_km"
        if col in d and d[col].notna().any():
            print(f"   {p}: nuestro centroide a foco MIROVA: n={int(d[col].notna().sum())}, mediana {d[col].median():.2f} km, p90 {d[col].quantile(.9):.2f}, <= 1 km en {int((d[col]<=1.0).sum())}")
