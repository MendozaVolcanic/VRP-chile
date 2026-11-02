# vch_06: las 4 pasadas MODIS con alerta MIROVA que K no publica (JSON de main). Salida: salidas/v06_perdidas_modis.txt
import json
d = json.load(open('copia/data/mirova_equivalent/NevadosDeChillan.json'))
want = {'2026-09-29 07:20', '2026-10-12 07:20', '2026-10-15 01:05', '2026-10-25 07:20'}
for r in d['records']:
    if r['datetime_utc'][:16] in want and r['sensor'].startswith('MODIS'):
        pc = r.get('primary_cluster') or {}
        print(r['datetime_utc'][:16], r['sensor'], 'z', r['sensor_zenith_deg'], 'n_anom', r['n_anomalous_pixels'], 'pc_n', pc.get('n_pixels'), 'pc_vrp', pc.get('vrp_mw'), 'pc_dist', pc.get('centroid_dist_km'), 'vrp_mw', r['vrp_mw'], 't_max', r['t_max_k'], 't_bg', r['t_bg_k'], 'dc', r.get('distance_class'), 'fhs', r.get('final_hotspot_source'), 'sha', (r.get('regimen') or {}).get('codigo_sha', '')[:8])
