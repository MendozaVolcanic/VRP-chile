"""S104 — Probe NTI de una noche de ALERTA REAL (Villarrica 2026-05-22, MIROVA
VIIRS375 VRP 0.55 MW @ 0.53 km). Pregunta decisiva: ¿la lava real produce una
firma espectral (MIR−TIR) integrada en el cráter, aunque ningún píxel individual
pase el NTI? Si sí → el fix correcto es integrar (L_MIR − L_TIR) en el Test1, no
co-validar per-píxel (que lo apaga, ver A/B run 27186289487).

Corre en GitHub Actions (secrets EARTHDATA). Vuelca: campo NTI, integral de
(L_MIR − L_TIR) sobre ROI 3km vs el resto, dónde está el NTI máx, PNG del NTI.
"""
import sys, io, math
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.fetch import search_granules, download_granules, _match_granules, auth
from pipeline.process_viirs import read_viirs_l1b, read_viirs_geo
from pipeline.test1_integrated import bt_to_radiance_um

auth()
VLAT, VLON = -39.420227, -71.939876
HERE = Path(__file__).parent
DEST = HERE / "granules_nti"; DEST.mkdir(exist_ok=True)
OUT = HERE / "out_nti"; OUT.mkdir(exist_ok=True)
DATE = datetime(2026, 5, 22)
I04_L, I05_L = 3.74, 11.45


def gname(g):
    try: return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception: return str(g)[:60]


def analyze(sat, l1b_path, geo_path):
    bands = read_viirs_l1b(l1b_path)
    g = read_viirs_geo(geo_path)
    lat, lon = g["lat"], g["lon"]
    if "I04" not in bands or "I05" not in bands:
        print(f"  {sat}: falta I04/I05"); return
    i04, i05 = bands["I04"], bands["I05"]
    dN = (lat - VLAT) * 111320
    dE = (lon - VLON) * 111320 * math.cos(VLAT * math.pi / 180)
    dist = np.hypot(dN, dE) / 1000.0
    valid = np.isfinite(i04) & np.isfinite(i05)
    # NTI con radiancias (como MIROVA)
    L4 = bt_to_radiance_um(i04, I04_L)
    L5 = bt_to_radiance_um(i05, I05_L)
    nti = (L4 - L5) / (L4 + L5)
    roi3 = (dist <= 3) & valid
    if roi3.sum() == 0:
        print(f"  {sat}: ROI<=3km vacío"); return
    # NTI máx en el ROI 3km y su posición
    n = np.where(roi3, nti, -np.inf)
    iy, ix = np.unravel_index(np.argmax(n), n.shape)
    print(f"  {sat}: NTI_max ROI3km = {nti[iy,ix]:.4f} @ {dist[iy,ix]:.2f}km "
          f"({dN[iy,ix]:+.0f}N,{dE[iy,ix]:+.0f}E)", flush=True)
    # NTI de fondo (mediana del anillo 1-3km)
    ring = (dist > 1) & (dist <= 3) & valid
    nti_bg = float(np.median(nti[ring]))
    nti_std = float(np.median(np.abs(nti[ring] - nti_bg))) * 1.4826
    print(f"    NTI_bg={nti_bg:.4f} std={nti_std:.4f}  NTI_max-bg = {nti[iy,ix]-nti_bg:.4f} "
          f"({(nti[iy,ix]-nti_bg)/nti_std:.1f}σ)", flush=True)
    # firma integrada: Σ(L4-L5) en cráter (<1.5km) vs en el resto del ROI 3km
    core = (dist <= 1.5) & valid
    diff = L4 - L5
    print(f"    Σ(L_MIR-L_TIR) núcleo<1.5km = {np.sum(diff[core]):.1f}  "
          f"vs anillo 1.5-3km = {np.sum(diff[(dist>1.5)&(dist<=3)&valid]):.1f}", flush=True)
    # cuántos píxeles con NTI > bg+3σ (firma de lava) y dónde
    hot = roi3 & (nti > nti_bg + max(0.005, 3*nti_std))
    if hot.sum():
        ds = dist[hot]
        print(f"    píxeles NTI>bg+3σ (firma lava): {int(hot.sum())}  dist={np.round(np.sort(ds)[:6],2).tolist()}", flush=True)
    else:
        print(f"    píxeles NTI>bg+3σ: 0 (ningún píxel individual con firma de lava)", flush=True)
    # i04 crudo máx para contraste
    print(f"    BT I04 máx ROI3km = {i04[roi3].max():.1f}K  en cráter<1.5km = {i04[core].max():.1f}K", flush=True)
    # PNG del NTI
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        ys, xs = np.where(dist <= 6)
        y0,y1,x0,x1 = ys.min(),ys.max()+1,xs.min(),xs.max()+1
        sub=nti[y0:y1,x0:x1]; sl=lat[y0:y1,x0:x1]; so=lon[y0:y1,x0:x1]
        fig,ax=plt.subplots(figsize=(7,7))
        pc=ax.pcolormesh(so,sl,sub,shading="auto",cmap="RdBu_r")
        ax.plot(VLON,VLAT,"k*",ms=20,mec="w",label="cráter")
        th=np.linspace(0,2*np.pi,100)
        ax.plot(VLON+3/111.32/math.cos(VLAT*math.pi/180)*np.cos(th),VLAT+3/111.32*np.sin(th),"k--",lw=1)
        plt.colorbar(pc,label="NTI = (L_MIR−L_TIR)/(L_MIR+L_TIR)")
        ax.set_title(f"Villarrica {sat} 2026-05-22 — NTI (firma de lava)")
        ax.legend(); fig.savefig(OUT/f"nti_{sat}.png",dpi=110,bbox_inches="tight"); plt.close()
        print(f"    PNG: out_nti/nti_{sat}.png", flush=True)
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
        if any(t in nm for t in (".0548.",".0554.",".0542.",".0600.",".0530.",".0536.",".0524.",".0506.")):
            picked = (lg, gg); break
    if not picked and pairs: picked = pairs[0]
    if not picked: print("  sin pares"); continue
    print("  granule:", gname(picked[0]), flush=True)
    try:
        paths = download_granules([picked[0], picked[1]], DEST)
        l1b_path = next(p for p in paths if "02IMG" in p.name)
        geo_path = next(p for p in paths if "03IMG" in p.name)
    except Exception as e:
        print("  download/match FAIL", type(e).__name__, str(e)[:80]); continue
    analyze(sat, l1b_path, geo_path)

print("\nDONE", flush=True)
