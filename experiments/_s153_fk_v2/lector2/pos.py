import json, math, sys
def brg(lat1,lon1,lat2,lon2):
    p1,p2=math.radians(lat1),math.radians(lat2); dl=math.radians(lon2-lon1)
    x=math.sin(dl)*math.cos(p2); y=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(x,y))+360)%360
def hav(lat1,lon1,lat2,lon2):
    R=6371.0; p1,p2=math.radians(lat1),math.radians(lat2)
    a=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 2*R*math.asin(math.sqrt(a))
base, vol, clat, clon, mlat, mlon = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
prefixes = sys.argv[7].split(',')
for arm in ['_s146_ab_control','_s149_ab_sin_test1_b22_max']:
    recs=json.load(open(base+'/'+arm+'/'+vol+'.json'))['records']
    for r in recs:
        t=r['datetime_utc']
        if any(t.startswith(p) for p in prefixes) and r['sensor'] in ('VIIRS_SNPP','VIIRS_NOAA20','VIIRS_NOAA21'):
            pc=r.get('primary_cluster') or {}
            la=pc.get('centroid_lat'); lo=pc.get('centroid_lon')
            if la is None: la,lo=pc.get('lat'),pc.get('lon')
            s=f"{arm[:12]} {t} {r['sensor']} cls={r['distance_class']} zen={r['sensor_zenith_deg']} pc_vrp={pc.get('vrp_mw')} "
            if la is not None:
                s+=f"pc=({la:.4f},{lo:.4f}) d_crat={hav(clat,clon,la,lo):.2f} brg={brg(clat,clon,la,lo):.0f} d_mref={hav(mlat,mlon,la,lo):.2f} brg_mref={brg(mlat,mlon,la,lo):.0f}"
            else:
                s+='pc keys='+str(list(pc.keys()))
            print(s)
