#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""S99 audit: confirmar mecanismo del 19x de Tupungatito en magnitud.
Read-only. Escribe SOLO a experiments/_s99_audit/.
Ningun numero a mano: todo derivado aqui.
A61: auditoria ESPACIAL (pixel->crater)."""
import sys, io, json, math, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
JSON = os.path.join(ROOT, "data/mirova_equivalent/Tupungatito.json")
TIFDIR = os.path.join(ROOT, "../mirova-tif-archive/data/tif/Tupungatito")

# crater (vent) anchor from volcanoes.yaml (Tupungatito vent_lat/lon)
CRATER_LAT = -33.389044
CRATER_LON = -69.826374
INNER_KM = 7.0
CORE_KM = 0.75  # F5' Nucleo radius

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

d = json.load(open(JSON, encoding='utf-8'))
recs = d['records']

def is_v375(s):
    s = str(s)
    return 'VIIRS' in s and '750' not in s

def month(r):
    return r.get('datetime_utc', '')[:7]

OUT = {}

# ---- Step 1: path composition big vs small (VIIRS375) ----
v375 = [r for r in recs if is_v375(r.get('sensor'))]
big = [r for r in v375 if (r.get('n_anomalous_pixels') or 0) >= 20]
small = [r for r in v375 if 0 < (r.get('n_anomalous_pixels') or 0) <= 3]

def path_summary(group):
    rows = []
    for r in group:
        npx = r.get('n_anomalous_pixels') or 0
        nd = r.get('diag_n_dnti_ctx_path') or 0
        na = r.get('diag_n_nti_path') or 0   # path B (NTI absolute)
        nbt = r.get('diag_n_bt_path') or 0   # path A (BT)
        neti = r.get('diag_n_eti_path') or 0
        nsp = r.get('diag_n_second_pass_recapture') or 0
        nt1 = r.get('n_test1_pixels') or 0
        first = r.get('diag_n_first_pass_pixels') or 0
        rows.append(dict(dt=r.get('datetime_utc'), sensor=r.get('sensor'),
                         npx=npx, first_pass=first, dnti_ctx=nd, nti=na, bt=nbt,
                         eti=neti, second_pass=nsp, test1=nt1,
                         vrp=r.get('vrp_mw'), pc_vrp=(r.get('primary_cluster') or {}).get('vrp_mw'),
                         pc_npx=(r.get('primary_cluster') or {}).get('n_pixels'),
                         t_bg_k=r.get('t_bg_k'), month=month(r)))
    return rows

OUT['v375_total'] = len(v375)
OUT['v375_big_n'] = len(big)
OUT['v375_small_n'] = len(small)
OUT['big_rows'] = path_summary(big)
OUT['small_rows'] = path_summary(small)

# Aggregate path-D fraction of first-pass detections for big records
# Limitation: per-pixel path NOT persisted. diag_n_*_path are FIRST-PASS path counts.
def frac_dnti(rows):
    out = []
    for x in rows:
        denom = (x['dnti_ctx'] + x['nti'] + x['bt'] + x['eti'])
        f = (x['dnti_ctx'] / denom) if denom else None
        out.append(f)
    return out

OUT['big_dnti_frac_of_firstpass_paths'] = frac_dnti(OUT['big_rows'])

# ---- Step 2 & 5: spatial distribution of anomaly_pixels in a big April/May record ----
def pick_big_aprmay(group):
    cand = [r for r in group if month(r) >= '2026-04']
    cand = [r for r in cand if r.get('anomaly_pixels')]
    if not cand:
        cand = [r for r in group if r.get('anomaly_pixels')]
    if not cand:
        return None
    return max(cand, key=lambda r: r.get('n_anomalous_pixels') or 0)

ex = pick_big_aprmay(big)
spatial = None
if ex:
    aps = ex['anomaly_pixels']
    dists = []
    for p in aps:
        dc = haversine(p['lat'], p['lon'], CRATER_LAT, CRATER_LON)
        dists.append(dc)
    dists_sorted = sorted(dists)
    n = len(dists)
    in_core = sum(1 for x in dists if x <= CORE_KM)
    in_inner = sum(1 for x in dists if x <= INNER_KM)
    # centroid of anomaly pixels
    clat = sum(p['lat'] for p in aps)/n
    clon = sum(p['lon'] for p in aps)/n
    cdist = haversine(clat, clon, CRATER_LAT, CRATER_LON)
    def pct(q):
        i = min(int(q*(n-1)+0.5), n-1)
        return dists_sorted[i]
    spatial = dict(
        dt=ex['datetime_utc'], sensor=ex['sensor'], n_anom=ex.get('n_anomalous_pixels'),
        n_anomaly_pixels_listed=n, t_bg_k=ex.get('t_bg_k'), t_max_k=ex.get('t_max_k'),
        vrp_mw=ex.get('vrp_mw'), pc=ex.get('primary_cluster'),
        dist_min=dists_sorted[0], dist_p25=pct(.25), dist_median=pct(.5),
        dist_p75=pct(.75), dist_max=dists_sorted[-1],
        n_in_core_0p75=in_core, n_in_inner_7=in_inner, n_total=n,
        anom_centroid_lat=clat, anom_centroid_lon=clon, anom_centroid_dist_km=cdist,
        all_dists=[round(x,3) for x in dists_sorted],
    )
OUT['spatial_example'] = spatial

# ---- Step 3: t_bg_k range of big records ----
tbgs = [r.get('t_bg_k') for r in big if r.get('t_bg_k') is not None]
if tbgs:
    tbgs_s = sorted(tbgs)
    OUT['big_tbg'] = dict(
        n=len(tbgs), min=tbgs_s[0], median=tbgs_s[len(tbgs_s)//2], max=tbgs_s[-1],
        n_below_270=sum(1 for x in tbgs if x < 270),
        n_270_290=sum(1 for x in tbgs if 270 <= x <= 290),
        n_above_290=sum(1 for x in tbgs if x > 290),
        values=tbgs_s,
    )

# ---- Step 4: TIF MIROVA ----
tif_report = {'dir_exists': os.path.isdir(TIFDIR)}
tifs = sorted(glob.glob(os.path.join(TIFDIR, '*.tif'))) if os.path.isdir(TIFDIR) else []
tif_report['n_tifs'] = len(tifs)
tif_report['tif_list_tail'] = [os.path.basename(t) for t in tifs[-10:]]
if tifs:
    try:
        import rasterio
        import numpy as np
        # pick most recent
        tpath = tifs[-1]
        tif_report['analyzed'] = os.path.basename(tpath)
        with rasterio.open(tpath) as ds:
            arr = ds.read(1).astype('float64')
            nod = ds.nodata
            transform = ds.transform
            crs = str(ds.crs)
            tif_report['shape'] = list(arr.shape)
            tif_report['crs'] = crs
            tif_report['nodata'] = nod
            mask = np.isfinite(arr)
            if nod is not None:
                mask &= (arr != nod)
            pos = mask & (arr > 0)
            tif_report['n_finite'] = int(mask.sum())
            tif_report['n_positive'] = int(pos.sum())
            if pos.any():
                vals = arr[pos]
                tif_report['pos_min'] = float(vals.min())
                tif_report['pos_max'] = float(vals.max())
                tif_report['pos_sum'] = float(vals.sum())
                # peak location
                ij = np.unravel_index(np.nanargmax(np.where(pos, arr, -np.inf)), arr.shape)
                row, col = int(ij[0]), int(ij[1])
                x, y = rasterio.transform.xy(transform, row, col)
                tif_report['peak_xy_crs'] = [x, y]
                # transform to lon/lat if not geographic
                try:
                    from rasterio.warp import transform as warp_t
                    lon, lat = warp_t(ds.crs, 'EPSG:4326', [x], [y])
                    plon, plat = lon[0], lat[0]
                    tif_report['peak_lon'] = plon
                    tif_report['peak_lat'] = plat
                    tif_report['peak_dist_to_crater_km'] = haversine(plat, plon, CRATER_LAT, CRATER_LON)
                    # weighted centroid of positive pixels
                    rows_i, cols_i = np.where(pos)
                    w = arr[pos]
                    xs, ys = rasterio.transform.xy(transform, list(rows_i), list(cols_i))
                    xs = np.array(xs); ys = np.array(ys)
                    lons, lats = warp_t(ds.crs, 'EPSG:4326', list(xs), list(ys))
                    lons = np.array(lons); lats = np.array(lats)
                    cx = float((lons*w).sum()/w.sum())
                    cy = float((lats*w).sum()/w.sum())
                    tif_report['weighted_centroid_lon'] = cx
                    tif_report['weighted_centroid_lat'] = cy
                    tif_report['weighted_centroid_dist_to_crater_km'] = haversine(cy, cx, CRATER_LAT, CRATER_LON)
                    # how many positive pixels within inner 7 km of crater
                    dd = [haversine(la, lo, CRATER_LAT, CRATER_LON) for la, lo in zip(lats, lons)]
                    tif_report['n_pos_within_7km'] = int(sum(1 for x in dd if x <= 7))
                    tif_report['n_pos_within_0p75km'] = int(sum(1 for x in dd if x <= 0.75))
                except Exception as e:
                    tif_report['warp_error'] = repr(e)
    except Exception as e:
        tif_report['error'] = repr(e)
else:
    tif_report['note'] = 'no tif files'
OUT['tif'] = tif_report

# Write JSON of derived numbers
with open(os.path.join(ROOT, 'experiments/_s99_audit/tupun_mechanism.json'), 'w', encoding='utf-8') as f:
    json.dump(OUT, f, indent=1, default=str)

# Console summary
print("V375 total:", OUT['v375_total'], "big(>=20):", OUT['v375_big_n'], "small(<=3):", OUT['v375_small_n'])
fr = [x for x in OUT['big_dnti_frac_of_firstpass_paths'] if x is not None]
if fr:
    print("big dNTI-ctx frac of first-pass path counts: min %.2f median %.2f max %.2f n=%d" % (
        min(fr), sorted(fr)[len(fr)//2], max(fr), len(fr)))
if spatial:
    print("Spatial example:", spatial['dt'], spatial['sensor'], "n_anom", spatial['n_anom'],
          "listed", spatial['n_anomaly_pixels_listed'])
    print("  dist crater median %.2f km, p25 %.2f, p75 %.2f, max %.2f" % (
        spatial['dist_median'], spatial['dist_p25'], spatial['dist_p75'], spatial['dist_max']))
    print("  in core(0.75km): %d / %d ; in inner(7km): %d / %d" % (
        spatial['n_in_core_0p75'], spatial['n_total'], spatial['n_in_inner_7'], spatial['n_total']))
    print("  anom centroid dist to crater %.2f km" % spatial['anom_centroid_dist_km'])
if 'big_tbg' in OUT:
    b = OUT['big_tbg']
    print("big t_bg_k: min %.1f median %.1f max %.1f | <270:%d 270-290:%d >290:%d" % (
        b['min'], b['median'], b['max'], b['n_below_270'], b['n_270_290'], b['n_above_290']))
print("TIF:", tif_report.get('n_tifs'), "files; analyzed", tif_report.get('analyzed'),
      "n_pos", tif_report.get('n_positive'), "peak_dist_km", tif_report.get('peak_dist_to_crater_km'))
print("DONE")
