"""S107 §1 blindaje TIF/R2 del FN MODIS Láscar (D12).

Pregunta: en las noches que el archivo TIF cubre (solo 2026-05-08..20; el grueso
Ene-Feb ya fue sobrescrito por MIROVA), ¿el campo de radiancia MIROVA muestra una
anomalía REAL en el cráter (confirmando nuestro cluster) y el píxel del Salar es
una feature aparte? Método R2 (S69/A20/A24): NO usar el máximo global del TIF
(puede ser Salar/borde/diurno); mirar la anomalía LOCAL dentro de ~3 km del cráter
en adquisiciones NOCTURNAS (MIR solo nocturno).

Read-only. No toca pipeline ni data operacional.
"""
import csv, json, math, re, os
import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform

ARCH = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive"
REPO = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
CRATER = (-23.36293, -67.731416)  # volcanoes.yaml Láscar vent
R_NEAR_KM = 3.0                    # R2 radio cráter
SALAR_LON_MAX = -67.85            # oeste del grid ~ Salar/borde

def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

# --- 1. archivo TIF: adquisiciones MODIS Láscar ---
rows = [r for r in csv.DictReader(open(os.path.join(ARCH, "index.csv"), encoding="utf-8"))
        if r["volcano"] == "Lascar" and r["sensor"] == "MODIS"]
acqs = {}
for r in rows:
    m = re.search(r"(\d{8})_(\d{6})", r["tif_path"])
    if not m:
        continue
    ts = m.group(0)
    dt = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:8]}T{m.group(2)[:2]}:{m.group(2)[2:4]}:{m.group(2)[4:6]}Z"
    acqs[ts] = (dt, os.path.join(ARCH, r["tif_path"]))

# --- 2. nuestros records MODIS Láscar ---
recs = [r for r in json.load(open(os.path.join(REPO, "data/mirova_equivalent/Lascar.json")))["records"]
        if str(r.get("sensor", "")).startswith("MODIS")]
def rec_dt(r):
    s = r.get("datetime_utc", "")
    return s
import datetime as _dt
def parse(s):
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        d = _dt.datetime.fromisoformat(s)
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return d
recs_p = [(parse(r.get("datetime_utc","")), r) for r in recs]
recs_p = [(d, r) for d, r in recs_p if d]

def match_record(dt_iso):
    t = parse(dt_iso)
    best = None; bestd = 1e9
    for d, r in recs_p:
        delta = abs((d - t).total_seconds())
        if delta < bestd:
            bestd = delta; best = r
    return (best, bestd) if bestd <= 3600 else (None, bestd)

def tif_peak_near(path, center, r_km):
    """máx del campo dentro de r_km del centro -> (val, lat, lon, dist). También global y Salar."""
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(float)
        if ds.nodata is not None:
            a = np.where(a == ds.nodata, np.nan, a)
        H, W = a.shape
        rows_i, cols_i = np.mgrid[0:H, 0:W]
        xs, ys = rasterio.transform.xy(ds.transform, rows_i.ravel(), cols_i.ravel())
        lon = np.array(xs).reshape(H, W); lat = np.array(ys).reshape(H, W)
        if ds.crs and ds.crs.to_epsg() != 4326:
            lo, la = rio_transform(ds.crs, "EPSG:4326", lon.ravel(), lat.ravel())
            lon = np.array(lo).reshape(H, W); lat = np.array(la).reshape(H, W)
        # distancia al cráter por píxel (aprox plana, suficiente a esta escala)
        dkm = np.sqrt(((lat-center[0])*111.0)**2 + ((lon-center[1])*111.0*math.cos(math.radians(center[0])))**2)
        med = float(np.nanmedian(a))
        # near crater
        nearmask = (dkm <= r_km) & ~np.isnan(a)
        if nearmask.any():
            sub = np.where(nearmask, a, -np.inf)
            i = np.unravel_index(np.nanargmax(sub), a.shape)
            near = (float(a[i]), float(lat[i]), float(lon[i]), float(dkm[i]))
        else:
            near = None
        # global
        gi = np.unravel_index(np.nanargmax(a), a.shape)
        glob = (float(a[gi]), float(lat[gi]), float(lon[gi]), float(dkm[gi]))
        # salar region (oeste)
        salmask = (lon < SALAR_LON_MAX) & ~np.isnan(a)
        if salmask.any():
            ss = np.where(salmask, a, -np.inf)
            si = np.unravel_index(np.nanargmax(ss), a.shape)
            sal = (float(a[si]), float(lat[si]), float(lon[si]), float(dkm[si]))
        else:
            sal = None
        crater_val = float(a[H//2, W//2])  # centro del grid = cráter (grilla MIROVA centrada)
        return dict(median=med, near=near, glob=glob, sal=sal, crater_center_val=crater_val,
                    vmin=float(np.nanmin(a)), vmax=float(np.nanmax(a)))

print(f"{'acq_utc':<20} {'D/N':3} {'rec_dc':>7} {'rec_cl_d':>8} {'rec_loose_d':>11} | "
      f"{'near3km_val':>11} {'near_d':>7} | {'glob_d':>7} {'glob_val':>8} | {'sal_val':>8} | {'med':>6}")
print("-"*135)
for ts in sorted(acqs):
    dt_iso, path = acqs[ts]
    hh = int(ts[9:11])
    dn = "NIGHT" if 2 <= hh <= 10 else "day"  # UTC; Chile~UTC-4 -> noche 02-10 UTC aprox
    rec, dd = match_record(dt_iso)
    if rec:
        dc = rec.get("distance_class", "?")
        pc = rec.get("primary_cluster") or {}
        cl_d = pc.get("centroid_dist_km")
        loose_d = rec.get("final_hotspot_dist_km") or rec.get("hotspot_dist_km")
    else:
        dc = "-"; cl_d = None; loose_d = None
    try:
        pk = tif_peak_near(path, CRATER, R_NEAR_KM)
    except Exception as e:
        print(f"{dt_iso:<20} {dn:3} ERR {e}")
        continue
    near = pk["near"]; glob = pk["glob"]; sal = pk["sal"]
    cl_s = f"{cl_d:.2f}" if isinstance(cl_d,(int,float)) else "-"
    lo_s = f"{loose_d:.2f}" if isinstance(loose_d,(int,float)) else "-"
    near_s = f"{near[0]:.3f}" if near else "-"
    near_d = f"{near[3]:.2f}" if near else "-"
    glob_d = f"{glob[3]:.1f}" if glob else "-"
    glob_v = f"{glob[0]:.3f}" if glob else "-"
    sal_v = f"{sal[0]:.3f}" if sal else "-"
    print(f"{dt_iso:<20} {dn:3} {dc:>7} {cl_s:>8} {lo_s:>11} | "
          f"{near_s:>11} {near_d:>7} | {glob_d:>7} {glob_v:>8} | {sal_v:>8} | {pk['median']:.3f}")
