"""
S104 — Instrumented ROI probe: ¿dónde está el calor CRUDO de VIIRS I04 en
Villarrica respecto al cráter? (audit offset NW, doc AUDIT_S104).

NO replica los paths de detección (evita A48): solo carga el campo de BT I04 con
las funciones EXACTAS del pipeline (read_viirs_l1b / read_viirs_geo) y reporta
dónde está el píxel más caliente real dentro del ROI, vs el cráter.

Pensado para correr en GitHub Actions (secrets EARTHDATA_USERNAME/PASSWORD →
earthaccess strategy=environment). Vuelca reporte de texto + npz del ROI + PNG.

Noche objetivo: 2026-05-17 ~05:48 UTC (ALERTA MIROVA VRP 0.21 @ 0.84 km).
"""
import sys, io, math, os
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.fetch import search_granules, download_granules, _match_granules, auth
from pipeline.process_viirs import read_viirs_l1b, read_viirs_geo

auth()  # login earthaccess (environment en Actions / netrc local)

VLAT, VLON = -39.420227, -71.939876
HERE = Path(__file__).parent
DEST = HERE / "granules"; DEST.mkdir(exist_ok=True)
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
DATE = datetime(2026, 5, 17)

def gname(g):
    try: return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        try: return g["umm"]["GranuleUR"]
        except Exception: return str(g)[:60]

def analyze(sat, l1b_path, geo_path):
    bands = read_viirs_l1b(l1b_path)
    g = read_viirs_geo(geo_path)
    lat, lon = g["lat"], g["lon"]
    if "I04" not in bands:
        print(f"  {sat}: sin I04"); return
    i04 = bands["I04"]; i05 = bands.get("I05")
    dN = (lat - VLAT) * 111320
    dE = (lon - VLON) * 111320 * math.cos(VLAT * math.pi / 180)
    dist = np.hypot(dN, dE) / 1000.0
    roi = dist <= 10
    valid = roi & np.isfinite(i04)
    print(f"  {sat}: pixeles ROI<=10km validos = {int(valid.sum())}", flush=True)
    if valid.sum() == 0: return
    bt = np.where(valid, i04, -np.inf)
    iy, ix = np.unravel_index(np.argmax(bt), bt.shape)
    print(f"    BT_max CRUDO = {i04[iy,ix]:.1f} K @ ({lat[iy,ix]:.5f},{lon[iy,ix]:.5f}) "
          f"offset=({dN[iy,ix]:+.0f}N,{dE[iy,ix]:+.0f}E)={dist[iy,ix]:.2f}km", flush=True)
    vals = i04[valid]
    print(f"    ROI BT: median={np.median(vals):.1f} p95={np.percentile(vals,95):.1f} max={vals.max():.1f}", flush=True)
    order = np.argsort(bt.ravel())[::-1][:5]
    print("    top-5 (BT, dist_km, N_m, E_m):", flush=True)
    for k in order:
        yy, xx = np.unravel_index(k, bt.shape)
        print(f"      {i04[yy,xx]:.1f} K  {dist[yy,xx]:.2f} km  ({dN[yy,xx]:+.0f},{dE[yy,xx]:+.0f})", flush=True)
    near = (dist <= 2) & np.isfinite(i04)
    if near.sum():
        print(f"    BT_max dentro 2km crater = {i04[near].max():.1f} K  (ROI max {vals.max():.1f} K, "
              f"dif {vals.max()-i04[near].max():.1f} K)", flush=True)
    # dump npz del ROI recortado (bounding box de roi)
    ys, xs = np.where(roi)
    y0,y1,x0,x1 = ys.min(),ys.max()+1,xs.min(),xs.max()+1
    np.savez_compressed(OUT / f"roi_{sat}.npz",
        lat=lat[y0:y1,x0:x1], lon=lon[y0:y1,x0:x1], i04=i04[y0:y1,x0:x1],
        i05=(i05[y0:y1,x0:x1] if i05 is not None else np.zeros((1,1))),
        vlat=VLAT, vlon=VLON)
    # PNG
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        sub = i04[y0:y1,x0:x1]; slat=lat[y0:y1,x0:x1]; slon=lon[y0:y1,x0:x1]
        fig, ax = plt.subplots(figsize=(7,7))
        pc = ax.pcolormesh(slon, slat, sub, shading="auto", cmap="inferno")
        ax.plot(VLON, VLAT, "c*", ms=22, mec="k", label="cráter (vent_lat)")
        # circulo inner 5km
        th=np.linspace(0,2*np.pi,100)
        ax.plot(VLON+5/111.32/math.cos(VLAT*math.pi/180)*np.cos(th), VLAT+5/111.32*np.sin(th), "c--", lw=1)
        plt.colorbar(pc, label="BT I04 (K)"); ax.set_title(f"Villarrica {sat} 2026-05-17 — campo crudo I04")
        ax.legend(loc="upper right")
        fig.savefig(OUT / f"roi_{sat}.png", dpi=110, bbox_inches="tight"); plt.close()
        print(f"    PNG guardado: out/roi_{sat}.png", flush=True)
    except Exception as e:
        print("    PNG fail:", e)

for sat in ["VIIRS_NOAA20", "VIIRS_SNPP", "VIIRS_NOAA21"]:
    print(f"\n=== {sat} ===", flush=True)
    try:
        l1b = search_granules(f"{sat}_L1B", VLAT, VLON, 25, DATE)
        geo = search_granules(f"{sat}_GEO", VLAT, VLON, 25, DATE)
    except Exception as e:
        print("  search FAIL", e); continue
    pairs = _match_granules(l1b, geo)
    picked = None
    for lg, gg in pairs:
        nm = gname(lg)
        if any(t in nm for t in (".0548.",".0554.",".0542.",".0600.",".0530.",".0536.")):
            picked = (lg, gg); break
    if not picked and pairs: picked = pairs[0]
    if not picked: print("  sin pares"); continue
    print("  granule:", gname(picked[0]), flush=True)
    try:
        paths = download_granules([picked[0], picked[1]], DEST)
    except Exception as e:
        print("  download FAIL", type(e).__name__, str(e)[:100]); continue
    try:
        l1b_path = next(p for p in paths if "02IMG" in p.name)
        geo_path = next(p for p in paths if "03IMG" in p.name)
    except StopIteration:
        print("  no se bajaron ambos archivos:", [p.name for p in paths]); continue
    analyze(sat, l1b_path, geo_path)

print("\nDONE", flush=True)
