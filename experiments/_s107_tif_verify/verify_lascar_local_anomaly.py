"""S107 §1 — R2 detrended: ¿el píxel del cráter es una anomalía LOCAL en el campo
B21 MIR de MIROVA, descontando el gradiente topográfico cráter-frío→Salar-tibio?

El campo B21 crudo (TIF) tiene gradiente de altura (Salar domina el máximo global, A69).
Para aislar la señal volcánica sub-píxel se descuenta el fondo LOCAL (anillo inmediato)
y se compara contra un punto de CONTROL frío equidistante en sector no-Salar (NE alto).

Read-only. Solo adquisiciones NOCTURNAS (MIR válido).
"""
import csv, json, math, re, os
import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform

ARCH = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive"
REPO = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
CRATER = (-23.36293, -67.731416)
CONTROL = (-23.28, -67.64)  # ~12 km NE, terreno alto NO-Salar (control frío)

def px_grid(ds):
    a = ds.read(1).astype(float)
    if ds.nodata is not None:
        a = np.where(a == ds.nodata, np.nan, a)
    H, W = a.shape
    ri, ci = np.mgrid[0:H, 0:W]
    xs, ys = rasterio.transform.xy(ds.transform, ri.ravel(), ci.ravel())
    lon = np.array(xs).reshape(H, W); lat = np.array(ys).reshape(H, W)
    if ds.crs and ds.crs.to_epsg() != 4326:
        lo, la = rio_transform(ds.crs, "EPSG:4326", lon.ravel(), lat.ravel())
        lon = np.array(lo).reshape(H, W); lat = np.array(la).reshape(H, W)
    return a, lat, lon

def nearest_px(lat, lon, pt):
    d = (lat - pt[0])**2 + (lon - pt[1])**2
    return np.unravel_index(np.argmin(d), d.shape)

def local_anomaly(a, r, c, inner=1, outer=4):
    """valor central menos mediana del anillo [inner..outer] px; y si es local-max 3x3."""
    H, W = a.shape
    val = a[r, c]
    ring = []
    for dr in range(-outer, outer+1):
        for dc in range(-outer, outer+1):
            if max(abs(dr), abs(dc)) <= inner:
                continue
            rr, cc = r+dr, c+dc
            if 0 <= rr < H and 0 <= cc < W and not np.isnan(a[rr, cc]):
                ring.append(a[rr, cc])
    bg = float(np.median(ring)) if ring else float("nan")
    # local max en 3x3
    neigh = [a[r+dr, c+dc] for dr in (-1,0,1) for dc in (-1,0,1)
             if 0 <= r+dr < H and 0 <= c+dc < W and not (dr==0 and dc==0) and not np.isnan(a[r+dr, c+dc])]
    is_locmax = all(val >= n for n in neigh) if neigh else False
    return val, bg, val - bg, is_locmax

# archive acquisitions
rows = [r for r in csv.DictReader(open(os.path.join(ARCH, "index.csv"), encoding="utf-8"))
        if r["volcano"] == "Lascar" and r["sensor"] == "MODIS"]
acqs = {}
for r in rows:
    m = re.search(r"(\d{8})_(\d{6})", r["tif_path"])
    if m:
        acqs[m.group(0)] = os.path.join(ARCH, r["tif_path"])

print(f"{'acq_utc':<16} {'hh':>2} | {'crater_val':>10} {'crater_bg':>9} {'cr_anom':>8} {'cr_lmax':>7} | "
      f"{'ctrl_val':>8} {'ctrl_bg':>8} {'ctrl_anom':>9} {'ctrl_lmax':>9}")
print("-"*110)
n_cr_pos = n_cr_lmax = n_ctrl_pos = n_ctrl_lmax = n_night = 0
cr_anoms = []; ctrl_anoms = []
for ts in sorted(acqs):
    hh = int(ts[9:11])
    if not (2 <= hh <= 10):   # solo noche (UTC, Chile~-4)
        continue
    n_night += 1
    with rasterio.open(acqs[ts]) as ds:
        a, lat, lon = px_grid(ds)
    cr = nearest_px(lat, lon, CRATER)
    ct = nearest_px(lat, lon, CONTROL)
    cv, cbg, ca, clm = local_anomaly(a, *cr)
    tv, tbg, ta, tlm = local_anomaly(a, *ct)
    cr_anoms.append(ca); ctrl_anoms.append(ta)
    if ca > 0: n_cr_pos += 1
    if clm: n_cr_lmax += 1
    if ta > 0: n_ctrl_pos += 1
    if tlm: n_ctrl_lmax += 1
    dt = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[9:11]}:{ts[11:13]}"
    print(f"{dt:<16} {hh:>2} | {cv:>10.3f} {cbg:>9.3f} {ca:>+8.3f} {str(clm):>7} | "
          f"{tv:>8.3f} {tbg:>8.3f} {ta:>+9.3f} {str(tlm):>9}")

print("-"*110)
print(f"NOCHES analizadas: {n_night}")
print(f"CRÁTER : anomalía local >0 en {n_cr_pos}/{n_night} ({100*n_cr_pos/n_night:.0f}%); "
      f"local-max 3x3 en {n_cr_lmax}/{n_night} ({100*n_cr_lmax/n_night:.0f}%); "
      f"anomalía mediana {np.median(cr_anoms):+.3f}")
print(f"CONTROL: anomalía local >0 en {n_ctrl_pos}/{n_night} ({100*n_ctrl_pos/n_night:.0f}%); "
      f"local-max 3x3 en {n_ctrl_lmax}/{n_night} ({100*n_ctrl_lmax/n_night:.0f}%); "
      f"anomalía mediana {np.median(ctrl_anoms):+.3f}")
print()
print("INTERPRETACIÓN: si CRÁTER tiene anomalía local + local-max sistemáticamente por")
print("encima del CONTROL, hay señal térmica real al cráter aun descontando el gradiente.")
