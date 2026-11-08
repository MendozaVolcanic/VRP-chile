import sys,io,runpy,collections,statistics as st,json,glob,os,contextlib
_b=io.StringIO()
with contextlib.redirect_stdout(_b): g=runpy.run_path('s2b.py')
sys.stdout.reconfigure(encoding='utf-8')
rows=g['rows']
for x in rows:
    if x['s']=='VIIRS375' and (x['q']==0 or x['p']==0 or x['q'] is None): print('V375',x['v'],x['t'],'MIROVA',x['vm'],'prod',x['p'],'sombra',x['q'])
    if x['s']=='VIIRS750' and (x['q']==0 or x['p']==0): print('V750',x['v'],x['t'],'MIROVA',x['vm'],'prod',x['p'],'sombra',x['q'])
c=collections.Counter()
for f in glob.glob(r'main\data\sombra_codigo_mirova\*.json'):
    for r in json.load(open(f,encoding='utf8'))['records']:
        if r['sensor'].startswith('VIIRS') and not r['sensor'].endswith('_750') and (r.get('vrp_mw') or 0)>0:
            fc=r.get('f5_core_vrp_mw'); pc=(r.get('primary_cluster') or {}).get('vrp_mw')
            c['con_pc']+=pc is not None; c['con_f5']+=fc is not None; c['f5_eq_pc']+= (fc is not None and pc is not None and abs(fc-pc)<1e-3); c['f5_menor']+=(fc is not None and pc is not None and fc<pc-1e-3); c['n']+=1; c['via_true']+=r.get('via_codigo_mirova') is True
print(c)
