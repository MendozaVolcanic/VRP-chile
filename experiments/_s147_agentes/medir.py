# -*- coding: utf-8 -*-
"""Que hay en el TIF de MIROVA en la posicion de nuestro pixel, contra su entorno."""
import json, numpy as np, rasterio, collections, math, sys
rng = np.random.default_rng(20260920)
F = json.load(open("master.json"))

def cls(f):
    t = set(f["ref_tipos"])
    if not t: return "SIN_REFERENCIA"
    if any(x.startswith("ALERTA") for x in t): return "MIROVA_ALERTA"
    if any(x.startswith("FALSO") for x in t): return "MIROVA_FALSO_POS"
    return "MIROVA_RUTINA0"

R_KM = 5.0   # radio del disco de entorno

def stats_en(a, rr, cc, r_cells):
    H, W = a.shape
    if not (0 <= rr < H and 0 <= cc < W): return None
    v = a[rr, cc]
    if not np.isfinite(v): return None
    y, x = np.ogrid[:H, :W]
    d2 = (y-rr)**2 + (x-cc)**2
    m = (d2 <= r_cells**2) & np.isfinite(a)
    vals = a[m]
    if vals.size < 30: return None
    med = np.median(vals); mad = np.median(np.abs(vals-med))*1.4826
    pctl = float((vals < v).mean())
    z = float((v-med)/mad) if mad > 0 else float("nan")
    # cuanto sobresale sobre el anillo inmediato (8 vecinos)
    nb = a[max(0,rr-1):rr+2, max(0,cc-1):cc+2].astype(float).copy()
    if nb.shape == (3,3): nb[1,1] = np.nan
    exc8 = float(v - np.nanmean(nb))
    esmax = bool(v >= np.nanmax(vals))
    return dict(v=float(v), pctl=pctl, z=z, exc8=exc8, es_max_disco=esmax, n_disco=int(vals.size))

out = []
for f in F:
    if f["tif_dmin"] != 0.0 or f["pc_lat"] is None: continue
    with rasterio.open(f["tif"]) as ds:
        a = ds.read(1).astype(float)
        resy_km = ds.res[1]*110.57
        rc = ds.index(f["pc_lon"], f["pc_lat"])
        r_cells = R_KM/resy_km
        s = stats_en(a, rc[0], rc[1], r_cells)
        # NULO: 120 celdas al azar de la misma imagen, a >6 km de la nuestra, mismo estadistico
        nul = []
        H, W = a.shape
        for _ in range(400):
            rr = int(rng.integers(0, H)); cc = int(rng.integers(0, W))
            if (rr-rc[0])**2 + (cc-rc[1])**2 < (6/resy_km)**2: continue
            t = stats_en(a, rr, cc, r_cells)
            if t: nul.append(t)
            if len(nul) >= 120: break
    out.append(dict(vol=f["vol"], t=f["t"], zen=f["zen"], src=f["src"], clase=cls(f),
                    pc_vrp=f["pc_vrp"], pc_n=f["pc_n"], pc_dist=f["pc_dist"], inner=f["inner"],
                    t_bg=f["t_bg_k"], ref_vrp=f["ref_vrp"], ref_dist=f["ref_dist"],
                    dentro=(f["pc_dist"] is not None and f["pc_dist"] <= f["inner"]),
                    fuera_raster=(s is None),
                    **({} if s is None else {"ours_"+k: v for k, v in s.items()}),
                    nul_pctl=float(np.median([x["pctl"] for x in nul])) if nul else None,
                    nul_z=float(np.median([x["z"] for x in nul])) if nul else None,
                    nul_esmax=float(np.mean([x["es_max_disco"] for x in nul])) if nul else None,
                    nul_pctl_p90=float(np.percentile([x["pctl"] for x in nul],90)) if nul else None,
                    nul_n=len(nul)))
json.dump(out, open("medido.json","w"), indent=0)
print("casos medidos (TIF exacto):", len(out), "fuera del raster:", sum(1 for o in out if o["fuera_raster"]))
