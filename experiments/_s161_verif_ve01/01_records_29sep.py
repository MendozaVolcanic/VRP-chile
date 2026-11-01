"""VE01-V: records de Tupungatito del 2026-09-29 entre 02 y 08 UTC.
Pregunta 1: si el record no existiera, esto imprime 0 filas (lo veria).
Pregunta 2: control positivo: imprime el conteo total y el de la noche entera."""
import json, math, sys
R = 'data/mirova_equivalent/Tupungatito.json'
d = json.load(open(R, encoding='utf-8'))
recs = d['records'] if isinstance(d, dict) else d
VENT = (-33.389044, -69.826374); CEN = (-33.42694, -69.80039)
def hav(a, b, c, e):
    R6 = 6371.0; p1, p2 = math.radians(a), math.radians(c)
    dp = p2 - p1; dl = math.radians(e - b)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R6*math.asin(math.sqrt(h))
def rumbo(a, b, c, e):
    y = math.sin(math.radians(e-b))*math.cos(math.radians(c))
    x = math.cos(math.radians(a))*math.sin(math.radians(c)) - math.sin(math.radians(a))*math.cos(math.radians(c))*math.cos(math.radians(e-b))
    return (math.degrees(math.atan2(y, x)) + 360) % 360
print('total records', len(recs))
noche = [r for r in recs if r['datetime_utc'].startswith('2026-09-29') or r['datetime_utc'].startswith('2026-09-28 2')]
print('records 28-sep 20h a 29-sep 23h', len(noche))
for r in recs:
    t = r['datetime_utc']
    if not ('2026-09-29 02' <= t <= '2026-09-29 08'):
        continue
    pc = r.get('primary_cluster') or {}
    fl, fo = r.get('final_hotspot_lat'), r.get('final_hotspot_lon')
    print('---', t, r['sensor'], r.get('granule'), 'zen', r.get('sensor_zenith_deg'), 'solzen', r.get('solar_zenith_deg'))
    print('   vrp_mw', r.get('vrp_mw'), 'distance_class', r.get('distance_class'), 'n_anom', r.get('n_anomalous_pixels'),
          'final', fl, fo, r.get('final_hotspot_dist_km'), r.get('final_hotspot_source'))
    if fl is not None:
        print('   final: dist vent %.2f km rumbo %.0f ; dist centro MIROVA %.2f km rumbo %.0f' % (
            hav(*VENT, fl, fo), rumbo(*VENT, fl, fo), hav(*CEN, fl, fo), rumbo(*CEN, fl, fo)))
    print('   pc', {k: pc.get(k) for k in pc if k not in ('pixels', 'members')})
    for p in (r.get('anomaly_pixels') or [])[:20]:
        la, lo = p.get('lat'), p.get('lon')
        print('   pix', {k: p[k] for k in p}, 'dvent %.2f r%.0f dcen %.2f' % (hav(*VENT, la, lo), rumbo(*VENT, la, lo), hav(*CEN, la, lo)))
    print('   processed', r.get('processed_utc'), 'first', r.get('first_processed_utc'))
