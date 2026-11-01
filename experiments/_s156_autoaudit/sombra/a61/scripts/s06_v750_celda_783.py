# -*- coding: utf-8 -*-
"""(2 y 3, refinado para VIIRS 750) a) Cuando MIROVA dijo 7,83 km en VIIRS 750 en pasadas con TIF, que celda del
TIF es su foco, y a que distancia queda de los pixeles de la sombra del 2026-10-10 05:54. b) Calibracion de las
miniaturas VIIRS 750 de PCC con vector de corrimiento (dE, dN) TIF->miniatura, en todas las alertas V750 con TIF;
y el maximo de la celda 05:54:02 corregido por ese vector.
Uso: python -I s06_v750_celda_783.py <worktree> <index_png.csv>"""
import json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio

WT = Path(sys.argv[1]); IDXPNG = Path(sys.argv[2]); BASE = Path(__file__).resolve().parents[1]
os.environ["VRP_TIF_CACHE"] = str(BASE / "bajados" / "tif_cache")
sys.path.insert(0, str(WT / "experiments" / "_s151_seleccion_mirova")); sys.path.insert(0, str(BASE / "scripts"))
import comun_tif as T  # noqa
import lascar_20261001 as L  # noqa
import subprocess
def png(path):
    dest = BASE / "bajados" / "png" / Path(path).name
    if not dest.exists():
        dest.write_bytes(subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
            f"repos/MendozaVolcanic/mirova-tif-archive/contents/{path}"], capture_output=True, check=True).stdout)
    return dest
VENT = (-40.525499, -72.146137)
rec = next(r for r in json.load(open(WT / "data/experimental_v2/PuyehueCordonCaulle.json", encoding="utf-8"))["records"]
           if r["sensor"] == "VIIRS_NOAA21_750" and r["datetime_utc"] == "2026-10-10 05:54")
PX = [(p["lat"], p["lon"], p["vrp_mw"]) for p in rec["anomaly_pixels"]][:4]
PC = (rec["primary_cluster"]["centroid_lat"], rec["primary_cluster"]["centroid_lon"])
ctl = [f for f in json.load(open(BASE / "salidas" / "s04_tif_control.json", encoding="utf-8")) if f["sensor"] == "VIIRS750"]
print("== a) Foco del TIF cuando MIROVA dijo 7,83 km (VIIRS 750)")
focos = []
for f in ctl:
    if abs(f["mirova_dist"] - 7.83) < 0.005 and "foco_anillo" in f:
        la, lo = f["foco_anillo"]
        d = [float(T.dist_km(p[0], p[1], la, lo)) for p in PX]
        print(f"   {f['t']} z {f['foco_anillo_z']} foco ({la},{lo}) d_centro {f['foco_anillo_d_centro']} | a px0..px3 de la sombra: "
              + ", ".join(f"{x:.2f}" for x in d) + f" | al centroide {float(T.dist_km(*PC, la, lo)):.2f} km")
        focos.append((la, lo))
u = sorted(set(focos)); print(f"   celdas distintas: {u}")
print("   (celda del TIF V750 ~0,75 km; un pixel nuestro 'en la celda' queda a <= ~0,53 km de su centro)")

print("\n== b) Calibracion V750 con vector de corrimiento")
ip = pd.read_csv(IDXPNG); ip = ip[(ip.volcano == "PuyehueCordonCaulle") & (ip.kind == "Latest10NTI") & (ip.sensor == "VIIRS750")].copy()
ip["lm"] = pd.to_datetime(ip.last_modified_utc, utc=True)
ix = T.indice(); ix = ix[(ix.vol == "PuyehueCordonCaulle") & (ix.sensor == "VIIRS750")]
vec = []
for f in ctl:
    if "foco_anillo" not in f or f["foco_anillo_z"] < 5:
        continue
    t = pd.Timestamp(f["t"])
    fila, _ = T.tif_de_pasada(ix, t)
    with rasterio.open(T.ruta_tif(fila)) as s:
        arr = s.read(1).astype(float); h, w = arr.shape; bnd = tuple(s.bounds)
    cand = ip[(ip.lm >= t) & (ip.lm <= t + pd.Timedelta(hours=6))].sort_values("lm")
    if cand.empty:
        print(f"   {t}: sin lamina"); continue
    cs = L.celdas(png(cand.iloc[0].png_path)); ref = L.zfield(L.tif_a_miniatura(arr)); rs = []
    for cc in cs:
        zc = L.zfield(cc); ok = np.isfinite(ref) & np.isfinite(zc)
        rs.append(float(np.corrcoef(np.clip(ref[ok], -10, 50), np.clip(zc[ok], -10, 50))[0, 1]) if zc[ok].std() > 0 else -9)
    k = int(np.argmax(rs)); zt = L.zfield(cs[k])
    v0, u0 = L.latlon_a_uv(*f["foco_anillo"], bnd, h, w); vi, ui = int(round(v0)), int(round(u0))
    win = zt[max(0, vi - 6):vi + 7, max(0, ui - 6):ui + 7]
    dv, du = np.unravel_index(int(np.nanargmax(win)), win.shape)
    la, lo = L.uv_a_latlon(max(0, vi - 6) + dv, max(0, ui - 6) + du, bnd)
    x, y = T.km_xy(la, lo, *f["foco_anillo"])
    zm = float(np.nanmax(win))
    print(f"   {t}: lamina {Path(cand.iloc[0].png_path).name} celda {k} r {rs[k]:.2f} z_mini {zm:.1f} corrimiento dE {float(x):+.2f} dN {float(y):+.2f} km")
    if zm >= 10:
        vec.append((float(x), float(y)))
vec = np.array(vec)
print(f"   laminas con foco visible (z>=10): {len(vec)}; corrimiento mediano dE {np.median(vec[:,0]):+.2f} dN {np.median(vec[:,1]):+.2f} km; "
      f"modulo mediano {np.median(np.hypot(vec[:,0], vec[:,1])):.2f}, max {np.max(np.hypot(vec[:,0], vec[:,1])):.2f}")
# el caso corregido
cas = json.load(open(BASE / "salidas" / "s05_miniaturas.json", encoding="utf-8"))["caso"]["VIIRS750"]["0"]
la, lo = cas["max_latlon"]
lat_c = la - np.median(vec[:, 1]) / 110.574
lon_c = lo - np.median(vec[:, 0]) / (111.320 * np.cos(np.radians(la)))
print(f"\n== c) maximo de la miniatura 05:54:02 (z {cas['z_max_celda']}) en ({la},{lo}); corregido por el corrimiento mediano: ({lat_c:.5f},{lon_c:.5f})")
for i, p in enumerate(PX):
    print(f"   a px{i} (vrp {p[2]}): sin corregir {float(T.dist_km(la, lo, p[0], p[1])):.2f} km, corregido {float(T.dist_km(lat_c, lon_c, p[0], p[1])):.2f} km")
print(f"   al centroide: sin corregir {float(T.dist_km(la, lo, *PC)):.2f}, corregido {float(T.dist_km(lat_c, lon_c, *PC)):.2f}; al vent corregido {float(T.dist_km(lat_c, lon_c, *VENT)):.2f}")
for (fl, fo) in u:
    print(f"   a la celda TIF de las 7,83 ({fl},{fo}): sin corregir {float(T.dist_km(la, lo, fl, fo)):.2f}, corregido {float(T.dist_km(lat_c, lon_c, fl, fo)):.2f}")
