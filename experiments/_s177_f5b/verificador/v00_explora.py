# -*- coding: utf-8 -*-
import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
S2 = json.load(open(r"C:\Users\nmend\vrp-temporales\s177_f5b\salidas\s02_manchas.json", encoding="utf-8"))
P8 = json.load(open(r"C:\Users\nmend\vrp-temporales\s177_f5b\orig\p8_clases.json", encoding="utf-8"))
print(len(S2), len(P8))
x=[o for o in P8 if o.get('png')][0]
print({k:(v if not isinstance(v,list) else v[:3]) for k,v in x.items()})
print(list(S2[0].keys()))
print('dup (sensor,dt,vol) en S2:', [k for k,c in collections.Counter((o['vol'],o['sensor'],o['dt']) for o in S2).items() if c>1])
print('png+panel repetidos:', [k for k,c in collections.Counter((o['png'],o['panel']) for o in S2).items() if c>1][:10])
d=json.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\chillan_base.json",encoding="utf-8"))
print(d.keys() if isinstance(d,dict) else type(d)); r=d['records'][0]; print(len(d['records']), {k:r[k] for k in r if k in('sensor','datetime_utc','sensor_zenith_deg','sensor_azimuth_deg','final_hotspot_lat','final_hotspot_lon','scan_angle_deg','satellite_azimuth_deg')})
print([k for k in r.keys()][:80])
ks=collections.Counter((r['sensor'],str(r['datetime_utc'])[:16]) for r in d['records'])
print('claves geo duplicadas', [k for k,c in ks.items() if c>1][:10])
