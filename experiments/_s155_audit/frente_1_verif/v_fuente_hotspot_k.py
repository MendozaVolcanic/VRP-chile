"""F1-15: distribucion de final_hotspot_source en records escritos por K (datetime >= 2026-09-18, reprocesados
con K segun v_regimen_control) y, aparte, >= 2026-10-18T09:57:30. Control: tramo 2026-08-01..09-18 (C0), donde
deben aparecer test1_roi; si alli tampoco aparecen, el campo no distingue regimen."""
import json, glob, collections
tr={'C0 08-01..09-18':('2026-08-01','2026-09-18'),'K 09-18..fin':('2026-09-18','2027'),'K NRT >=10-18 09:57':('2026-10-18T09:57:30','2027')}
for name,(a,b) in tr.items():
    c=collections.Counter(); cs=collections.Counter(); n=0
    for f in sorted(glob.glob('data/mirova_equivalent/*.json')):
        d=json.load(open(f,encoding='utf-8')); recs=d['records'] if isinstance(d,dict) else d
        for r in recs:
            if a<=r.get('datetime_utc','')<b:
                n+=1; s=r.get('final_hotspot_source'); c[s]+=1
                if s not in ('ctx_cluster','test1_roi','test1_nti_peak'):
                    pc=r.get('primary_cluster') or {}
                    cs[(r.get('sensor'),s,(pc.get('vrp_mw') or 0)>0, r.get('distance_class'))]+=1
    print(name,'n=',n,dict(c.most_common()))
    for k,v in cs.most_common(12): print('   no-ancla:',k,v)
