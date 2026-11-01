# -*- coding: utf-8 -*-
"""(3) Donde pone MIROVA su punto caliente en la miniatura de la pasada 2026-10-10 05:54:02 de PCC, con la
georreferencia de las miniaturas calibrada contra GeoTIFF de PCC (metodo de lascar_20261001.py, PR #809).
Laminas: las del archivo mirova-tif-archive (data/png), bajadas una a una por la API a bajados/png.
Uso: python -I s05_miniaturas.py <worktree> <index_png.csv>"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio

WT = Path(sys.argv[1]); IDXPNG = Path(sys.argv[2])
BASE = Path(__file__).resolve().parents[1]
os.environ["VRP_TIF_CACHE"] = str(BASE / "bajados" / "tif_cache")
sys.path.insert(0, str(WT / "experiments" / "_s151_seleccion_mirova"))
import comun_tif as T  # noqa
import lascar_20261001 as L  # noqa  (solo funciones: celdas, zfield, tif_a_miniatura, latlon_a_uv, uv_a_latlon)

PNG = BASE / "bajados" / "png"; PNG.mkdir(parents=True, exist_ok=True)
def png(path):
    dest = PNG / Path(path).name
    if not dest.exists():
        b = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                            f"repos/MendozaVolcanic/mirova-tif-archive/contents/{path}"], capture_output=True, check=True).stdout
        dest.write_bytes(b)
    return dest

VENT = (-40.525499, -72.146137)
ip = pd.read_csv(IDXPNG)
ip = ip[(ip.volcano == "PuyehueCordonCaulle") & (ip.kind == "Latest10NTI")].copy()
ip["lm"] = pd.to_datetime(ip.last_modified_utc, utc=True)
ctl = pd.DataFrame(json.load(open(BASE / "salidas" / "s04_tif_control.json", encoding="utf-8")))
ix = T.indice(); ix = ix[ix.vol == "PuyehueCordonCaulle"]
res = {"calibracion": [], "caso": {}}
bounds = {}
print("== 1. Calibracion de la georreferencia de las miniaturas de PCC contra TIF de la misma pasada")
for _, a in ctl.iterrows():
    t = pd.Timestamp(a["t"]); s = a["sensor"]
    if "foco_anillo" not in a or not isinstance(a["foco_anillo"], list) or a["foco_anillo_z"] < 8:
        continue
    fila, _m = T.tif_de_pasada(ix[ix.sensor == s], t)
    with rasterio.open(T.ruta_tif(fila)) as src:
        arr = src.read(1).astype(float); h, w = arr.shape; bnd = src.bounds
        if not src.crs.is_geographic:
            continue
    bounds.setdefault(s, (tuple(bnd), h, w))
    cand = ip[(ip.sensor == s) & (ip.lm >= t) & (ip.lm <= t + pd.Timedelta(hours=6))].sort_values("lm")
    if cand.empty:
        continue
    p = png(cand.iloc[0].png_path)
    ref = L.zfield(L.tif_a_miniatura(arr)); cs = L.celdas(p); rs = []
    for cc in cs:
        zc = L.zfield(cc); ok = np.isfinite(ref) & np.isfinite(zc)
        rs.append(float(np.corrcoef(np.clip(ref[ok], -10, 50), np.clip(zc[ok], -10, 50))[0, 1]) if zc[ok].std() > 0 else -9)
    k = int(np.argmax(rs)); zt = L.zfield(cs[k])
    v0, u0 = L.latlon_a_uv(*a["foco_anillo"], bnd, h, w); vi, ui = int(round(v0)), int(round(u0))
    win = zt[max(0, vi - 6):vi + 7, max(0, ui - 6):ui + 7]
    dv, du = np.unravel_index(int(np.nanargmax(win)), win.shape)
    la, lo = L.uv_a_latlon(max(0, vi - 6) + dv, max(0, ui - 6) + du, bnd)
    err = float(T.dist_km(la, lo, *a["foco_anillo"]))
    otras = [float(np.nanmax(L.zfield(c)[max(0, vi - 6):vi + 7, max(0, ui - 6):ui + 7])) for j, c in enumerate(cs) if j != k]
    f = {"t": str(t), "sensor": s, "lamina": Path(cand.iloc[0].png_path).name, "celda": k, "r": round(rs[k], 3),
         "z_mini": round(float(np.nanmax(win)), 1), "err_km": round(err, 3), "z_otras_mediana": round(float(np.median(otras)), 1)}
    res["calibracion"].append(f); print("  ", f)
    if len(res["calibracion"]) >= 30:
        break
cal = pd.DataFrame(res["calibracion"])
for s in ["VIIRS750", "VIIRS375"]:
    c = cal[cal.sensor == s]; b = c[c.z_mini >= 10]
    if len(c):
        print(f"   {s}: laminas {len(c)}; foco visible (z>=10) en {len(b)}; corrimiento TIF->miniatura mediana "
              f"{b.err_km.median() if len(b) else float('nan'):.2f} km, max {b.err_km.max() if len(b) else float('nan'):.2f}; "
              f"nulo otras celdas z mediana {c.z_otras_mediana.median():.1f}")

print("\n== 2. El caso: celda 05:54:02 (celda 0 de la lamina, cabecera leida en la imagen)")
recs = {p: json.load(open(WT / f"data/{p}/PuyehueCordonCaulle.json", encoding="utf-8"))["records"] for p in ["experimental_v2", "mirova_equivalent"]}
def rec(p, sen):
    return next(r for r in recs[p] if r["sensor"] == sen and r["datetime_utc"] == "2026-10-10 05:54")
CASO = {"VIIRS750": (WT / "experiments/_s156_autoaudit/sombra/20261010_083116_VIIRS750_Latest10NTI.png",
                     rec("experimental_v2", "VIIRS_NOAA21_750")),
        "VIIRS375": (png("data/png/PuyehueCordonCaulle/20261010_081020_VIIRS375_Latest10NTI.png"),
                     rec("mirova_equivalent", "VIIRS_NOAA21"))}
for s, (lam, r) in CASO.items():
    bnd, h, w = bounds[s]
    clat, clon = (bnd[1] + bnd[3]) / 2, (bnd[0] + bnd[2]) / 2
    cs = L.celdas(lam)
    pc = r["primary_cluster"]
    aps = sorted(r["anomaly_pixels"], key=lambda p: -(p["vrp_mw"] or 0))
    pmax = (aps[0]["lat"], aps[0]["lon"])
    out = {}
    for k in range(10):
        z = L.zfield(cs[k])
        vg, ug = np.unravel_index(int(np.nanargmax(z)), z.shape)
        lag, log = L.uv_a_latlon(vg, ug, bnd)
        def zen(lat, lon, rad=1):
            v, u = L.latlon_a_uv(lat, lon, bnd, h, w); vi, ui = int(round(v)), int(round(u))
            ww = z[max(0, vi - rad):vi + rad + 1, max(0, ui - rad):ui + rad + 1]
            return float(np.nanmax(ww)) if np.isfinite(ww).any() else float("nan")
        nul = []
        for ang in range(30, 360, 30):
            la, lo = T.rotar(*pmax, clat, clon, ang)
            v, u = L.latlon_a_uv(la, lo, bnd, h, w)
            if 3 <= v < L.LADO - 3 and 3 <= u < L.LADO - 3:
                nul.append(zen(la, lo))
        o = {"z_max_celda": round(float(np.nanmax(z)), 1), "max_latlon": [round(lag, 5), round(log, 5)],
             "max_d_px_mas_vrp_km": round(float(T.dist_km(lag, log, *pmax)), 2),
             "max_d_centroide_km": round(float(T.dist_km(lag, log, pc["centroid_lat"], pc["centroid_lon"])), 2),
             "max_d_vent_km": round(float(T.dist_km(lag, log, *VENT)), 2),
             "max_d_centro_raster_km": round(float(T.dist_km(lag, log, clat, clon)), 2),
             "z_en_px_mas_vrp": round(zen(*pmax), 1), "z_en_centroide": round(zen(pc["centroid_lat"], pc["centroid_lon"]), 1),
             "z_girado_mediana": round(float(np.nanmedian(nul)), 1), "z_girado_max": round(float(np.nanmax(nul)), 1), "n_girado": len(nul)}
        out[k] = o
        print(f"   {s} celda {k}: " + json.dumps(o, ensure_ascii=False))
    res["caso"][s] = out
(BASE / "salidas" / "s05_miniaturas.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
