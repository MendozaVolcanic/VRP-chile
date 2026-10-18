import json,glob,collections,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
R="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
B="C:/Users/nmend/AppData/Local/Temp/claude/mxd03_117/"
pob=json.load(open(B+'repo/experiments/_s151_mxd03_etiquetas/poblacion.json',encoding='utf-8'))
pred={}
for v,vv in pob['volcanes'].items():
    for g in vv['muestra']: pred[(v,g['clave'])]=g
G=[]
for p in glob.glob(B+'art/*/*.json'):
    d=json.load(open(p,encoding='utf-8'))
    if 'granulos' in d and 'job' in d:
        for g in d['granulos']:
            if g.get('estado')=='ok': g['volcan']=d['volcan']; G.append(g)
cache={}
def stored(v,dt,sensor):
    if v not in cache:
        x=json.load(open(R+'data/mirova_equivalent/%s.json'%v,encoding='utf-8'))
        x=x['records'] if isinstance(x,dict) else x
        cache[v]={(r['datetime_utc'],r['sensor']):r for r in x}
    return cache[v].get((dt,sensor))
rows=[]
for g in G:
    pr=pred[(g['volcan'],g['clave'])]
    s=stored(g['volcan'],pr['datetime_utc'],pr['sensor'])
    if s is None: continue
    C=g['c']; reg=s.get('regimen') or {}
    rows.append(dict(v=g['volcan'],dt=pr['datetime_utc'],sensor=pr['sensor'],clave=g['clave'],
      pv=s.get('product_version'),proc=s.get('processed_utc'),first=s.get('first_processed_utc'),sha=reg.get('codigo_sha'),
      n_s=s.get('n_anomalous_pixels'),n_c=C['n_anom'],t1=s.get('triggered_test1'),
      ocho=not g.get('c_igual_a_guardada'),zen=s.get('sensor_zenith_deg'),
      fp=s.get('diag_n_first_pass_pixels'),sp=s.get('diag_n_second_pass_recapture'),
      n_t1=s.get('n_test1_pixels'),tbg=s.get('t_bg_k'),nbg=s.get('diag_n_bg_anillo')))
json.dump(rows,open('C:/Users/nmend/AppData/Local/Temp/claude/deriva_123bis/tabla.json','w'),indent=0)
c=collections.Counter()
for r in rows:
    key=(r['proc'][:10] if r['proc'] else None, r['sha'][:8] if r['sha'] else None, 'igual' if r['n_s']==r['n_c'] else ('mas' if r['n_c']>r['n_s'] else 'menos'))
    c[key]+=1
for k,v in sorted(c.items(),key=lambda kv:str(kv[0])): print(k,v)
print('--- los 8')
for r in rows:
    if r['ocho']: print(r)
