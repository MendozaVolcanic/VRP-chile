#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, io, glob, os, math, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import rasterio
import numpy as np
from rasterio.warp import transform as warp_t

TIFDIR = "../mirova-tif-archive/data/tif/Tupungatito"
CRATER_LAT, CRATER_LON = -33.389044, -69.826374

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

# Analyze several recent VIIRS375 TIFs (May, the high-x month)
tifs = sorted(glob.glob(os.path.join(TIFDIR, '*VIIRS375*.tif')))
targets = [t for t in tifs if os.path.basename(t)[:6] in ('202605','202604')]
targets = targets[-6:] if targets else tifs[-3:]

results = []
for tpath in targets:
    rep = {'file': os.path.basename(tpath)}
    with rasterio.open(tpath) as ds:
        arr = ds.read(1).astype('float64')
        nod = ds.nodata
        rep['crs'] = str(ds.crs); rep['shape'] = list(arr.shape)
        mask = np.isfinite(arr)
        if nod is not None:
            mask &= (arr != nod)
        pos = mask & (arr > 0)
        rep['n_positive'] = int(pos.sum())
        if pos.any():
            rows_i, cols_i = np.where(pos)
            w = arr[pos]
            xs, ys = rasterio.transform.xy(ds.transform, list(rows_i), list(cols_i))
            lons, lats = warp_t(ds.crs, 'EPSG:4326', list(xs), list(ys))
            lons = np.array(lons); lats = np.array(lats); w = np.array(w)
            dd = np.array([haversine(la, lo, CRATER_LAT, CRATER_LON) for la, lo in zip(lats, lons)])
            # peak
            pk = int(np.argmax(w))
            rep['pos_max'] = float(w.max()); rep['pos_sum'] = float(w.sum())
            rep['peak_lat'] = float(lats[pk]); rep['peak_lon'] = float(lons[pk])
            rep['peak_dist_crater_km'] = float(dd[pk])
            # weighted centroid
            cx = float((lons*w).sum()/w.sum()); cy = float((lats*w).sum()/w.sum())
            rep['wcentroid_dist_crater_km'] = haversine(cy, cx, CRATER_LAT, CRATER_LON)
            rep['n_pos_within_7km'] = int((dd <= 7).sum())
            rep['n_pos_within_2km'] = int((dd <= 2).sum())
            rep['n_pos_within_0p75km'] = int((dd <= 0.75).sum())
            rep['dist_min'] = float(dd.min()); rep['dist_median'] = float(np.median(dd)); rep['dist_max'] = float(dd.max())
    results.append(rep)
    print(rep['file'], 'n_pos', rep.get('n_positive'), 'peak_dist_crater %.2f'%rep.get('peak_dist_crater_km',-1),
          'within7km', rep.get('n_pos_within_7km'), 'within0.75', rep.get('n_pos_within_0p75km'),
          'sum %.3f'%rep.get('pos_sum',0))

json.dump(results, open('experiments/_s99_audit/tif_analysis.json','w',encoding='utf-8'), indent=1)
print('DONE')
