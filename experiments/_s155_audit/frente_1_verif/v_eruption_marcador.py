"""F1-15 efecto: records K (datetime>=2026-09-18) con final_hotspot_source='eruption' y distance_class summit.
pixelesDelMarcador (frontend/index.html:1626) no los ancla: el marcador es anomaly_pixels[0]. Mide la distancia
de ese pixel (campo dist_km del pixel) contra final_hotspot_dist_km. Control: si anomaly_pixels[0] coincidiera
siempre con el final_hotspot, el defecto seria invisible (diferencia 0)."""
import json, glob
rows=[]
for f in sorted(glob.glob('data/mirova_equivalent/*.json')):
    d=json.load(open(f,encoding='utf-8')); recs=d['records'] if isinstance(d,dict) else d
    for r in recs:
        if r.get('datetime_utc','')>='2026-09-18' and r.get('final_hotspot_source')=='eruption' and r.get('distance_class')=='summit':
            ap=(r.get('anomaly_pixels') or [{}])[0]
            rows.append((__import__('os').path.basename(f)[:-5], r['datetime_utc'], r['sensor'], r.get('final_hotspot_dist_km'), ap.get('dist_km'), (r.get('primary_cluster') or {}).get('vrp_mw')))
print('n=',len(rows))
for x in rows: print(x)
far=[x for x in rows if x[4] is not None and x[3] is not None and abs(x[4]-x[3])>2]
print('marcador a >2 km del final_hotspot:',len(far))
