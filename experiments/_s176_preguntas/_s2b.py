# Exploratorio S176: produccion y sombra contra MIROVA en las MISMAS pasadas (tabla), sin decidir nada.
import json,glob,os,sys,io,collections,csv,statistics as st,datetime as dt,re
M=r'main\data'
cons=M+r'\mirova_reference\mirova_v1_snapshot\registro_vrp_consolidado.csv'
norm=lambda s:re.sub('[^a-z]','',s.lower().replace('cordon','').replace('caulle','caulle'))
vols=[os.path.basename(f)[:-5] for f in glob.glob(M+r'\sombra_codigo_mirova\*.json')]
mp={norm(v):v for v in vols}; mp.update({norm('Puyehue-Cordon Caulle'):'PuyehueCordonCaulle',norm('Nevados de Chillan'):'NevadosDeChillan',norm('Planchon Peteroa'):'PlanchonPeteroa'})
def buck(s): return 'MODIS' if s.startswith('MODIS') else ('VIIRS750' if s.endswith('_750') else 'VIIRS375')
SEN={'MODIS':'MODIS','VIIRS':'VIIRS750','VIIRS375':'VIIRS375'}
print('etiquetas csv',collections.Counter(r['Sensor'] for r in csv.DictReader(open(cons,encoding='utf8',errors='replace'))).most_common(6))
def load(d):
    o=collections.defaultdict(list)
    for v in vols:
        try: rs=json.load(open(f'{M}\{d}\{v}.json',encoding='utf8'))['records']
        except FileNotFoundError: continue
        for r in rs:
            t=dt.datetime.strptime(r['datetime_utc'][:16],'%Y-%m-%d %H:%M')
            o[(v,buck(r['sensor']))].append((t,r))
    return o
P=load('mirova_equivalent'); S=load('sombra_codigo_mirova')
def near(lst,t):
    best=None
    for tt,r in lst:
        d=abs((tt-t).total_seconds())
        if d<=150 and (best is None or d<best[0]): best=(d,r)
    return best[1] if best else None
def pub(r,sensor):
    if r is None: return None
    pc=r.get('primary_cluster')
    if not pc: return 0.0
    if r.get('distance_class') not in (None,'summit'): return 0.0
    if sensor=='VIIRS375' and r.get('f5_core_vrp_mw') is not None: return float(r['f5_core_vrp_mw'])
    return float(pc.get('vrp_mw') or 0)
rows=[]
for r in csv.DictReader(open(cons,encoding='utf8',errors='replace')):
    if r['Sensor'] not in SEN or not r['Fecha_Satelite_UTC']: continue
    if r['Tipo_Registro']!='ALERTA_TERMICA': continue
    if not ('2026-11-03'<=r['Fecha_Satelite_UTC']<'2026-11-07 12'): continue
    v=mp.get(norm(r['Volcan']))
    if not v: continue
    t=dt.datetime.strptime(r['Fecha_Satelite_UTC'][:19],'%Y-%m-%d %H:%M:%S'); s=SEN[r['Sensor']]
    vm=float(r['VRP_MW'])
    if vm<=0: continue
    a=near(P.get((v,s),[]),t); b=near(S.get((v,s),[]),t)
    
    if not (a and b and (a.get('solar_zenith_deg') or 0)>=90): continue
    rows.append(dict(v=v,s=s,t=t,vm=vm,p=pub(a,s),q=pub(b,s),a=a is not None,b=b is not None))
print('filas',len(rows))
out={}
for s in ('MODIS','VIIRS375','VIIRS750'):
    xs=[x for x in rows if x['s']==s]
    both=[x for x in xs if x['a'] and x['b'] and x['p'] is not None and x['q'] is not None]
    pp=[x['p']/x['vm'] for x in both if x['p']>0]; qq=[x['q']/x['vm'] for x in both if x['q']>0]
    co=[x for x in both if x['p']>0 and x['q']>0]
    print(s,'alertas MIROVA',len(xs),'con ambos records',len(both),'| prod publica',len(pp),'mediana',round(st.median(pp),3) if pp else None,'| sombra publica',len(qq),'mediana',round(st.median(qq),3) if qq else None,'| en comunes n',len(co),'prod',round(st.median([x['p']/x['vm'] for x in co]),3) if co else None,'sombra',round(st.median([x['q']/x['vm'] for x in co]),3) if co else None)
    byv=collections.defaultdict(list)
    for x in co: byv[x['v']].append(x)
    for v,l in sorted(byv.items()): print('   ',v,len(l),'prod',round(st.median([x['p']/x['vm'] for x in l]),3),'sombra',round(st.median([x['q']/x['vm'] for x in l]),3))
    for x in both:
        if x['q']<=0 and x['vm']>=1: print('    sombra no publica protegida:',x['v'],x['t'],x['vm'],'prod',x['p'])
        if x['p']<=0 and x['vm']>=1: print('    prod no publica protegida:',x['v'],x['t'],x['vm'],'sombra',x['q'])

print('--- dispersion (ratio en comunes) y negativos limpios')
def pct(l,p):
    l=sorted(l); return round(l[int(p*(len(l)-1))],3)
for s_ in ('VIIRS375','VIIRS750','MODIS'):
    co=[x for x in rows if x['s']==s_ and x['p'] and x['q'] and x['p']>0 and x['q']>0]
    for nm,k in (('prod','p'),('sombra','q')):
        l=[x[k]/x['vm'] for x in co]
        print(s_,nm,'p10',pct(l,.1),'p25',pct(l,.25),'p50',pct(l,.5),'p75',pct(l,.75),'p90',pct(l,.9),'dentro 0.7-1.4:',sum(.7<=v<=1.4 for v in l),'/',len(l))
neg=collections.Counter()
for r in csv.DictReader(open(cons,encoding='utf8',errors='replace')):
    if r['Sensor'] not in SEN or not ('2026-11-03'<=r['Fecha_Satelite_UTC']<'2026-11-07 12'): continue
    if r['Tipo_Registro']!='RUTINA' or float(r['VRP_MW'] or 0)!=0: continue
    v=mp.get(norm(r['Volcan']));
    if not v: continue
    t=dt.datetime.strptime(r['Fecha_Satelite_UTC'][:19],'%Y-%m-%d %H:%M:%S'); s_=SEN[r['Sensor']]
    a=near(P.get((v,s_),[]),t); b=near(S.get((v,s_),[]),t)
    if not(a and b and (a.get('solar_zenith_deg') or 0)>=90): continue
    neg[(s_,'n')]+=1; neg[(s_,'prod')]+=(pub(a,s_) or 0)>0; neg[(s_,'sombra')]+=(pub(b,s_) or 0)>0
print(sorted(neg.items()))
