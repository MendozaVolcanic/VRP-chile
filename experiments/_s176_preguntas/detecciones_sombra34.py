import json,glob,os,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
print('--- detecciones de la sombra de los 34')
for f in sorted(glob.glob(r'main\data\sombra_34\*.json')):
    v=os.path.basename(f)[:-5]
    for r in json.load(open(f,encoding='utf8'))['records']:
        if (r.get('vrp_mw') or 0)>0:
            d=r.get('diag_codigo_mirova') or {}
            print(f"{v:22s} {r['datetime_utc']} {r['sensor']:18s} vrp={r['vrp_mw']:<7} npx={r.get('n_anomalous_pixels')} clase={r.get('distance_class')} dist={r.get('final_hotspot_dist_km')} Tmax={r.get('t_max_k')} Tbg={r.get('t_bg_k')} zen={r.get('sensor_zenith_deg')} roi={d.get('roi')} motivo={d.get('motivo_vacio')}")
print('--- diag vacios / fallback')
c=collections.Counter()
for f in glob.glob(r'main\data\sombra_34\*.json'):
    for r in json.load(open(f,encoding='utf8'))['records']:
        d=r.get('diag_codigo_mirova') or {}
        c[(r.get('via_codigo_mirova'),d.get('motivo_vacio'),d.get('roi'))]+=1
print(c.most_common(20))
