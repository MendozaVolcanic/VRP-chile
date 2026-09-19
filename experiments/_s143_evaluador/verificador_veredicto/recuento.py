# Recuento independiente (no usa evaluar.py). Sólo reutiliza el predicado node del dashboard (A97).
import csv, json, math, re, sys, collections
from datetime import datetime, timezone, timedelta
ROOT=r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, ROOT+"/scripts"); sys.path.insert(0, ROOT)
import banco_paridad as bp, yaml
B='ab_fus'
V=["Isluga","Lascar","Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Chaiten","Villarrica","NevadosDeChillan"]
ARMS=sys.argv[1:] or ["_s142_ab_control","_s142_ab_literal"]
W=("2026-06-01","2026-08-31")
norm=lambda s: re.sub(r'[^a-z]','',s.lower())
NM={norm(v):v for v in V}
yml={v['name']:v for v in yaml.safe_load(open(ROOT+'/volcanoes.yaml',encoding='utf-8'))['volcanoes']}
CEN={v:(yml[v]['mirova_center_lat'],yml[v]['mirova_center_lon']) for v in V}
INNER=bp.inner_desde_html()
def hav(a,b,c,d):
    p=math.radians; x=math.sin(p(c-a)/2)**2+math.cos(p(a))*math.cos(p(c))*math.sin(p(d-b)/2)**2
    return 2*6371.0088*math.asin(math.sqrt(x))
# referencia
def _dist(r,src):
    try: d=float(r['Distancia_km'])
    except: d=None
    if src=='OCR' and not (d and d>0):
        m=re.search(r'dist\D*?([0-9]+(?:\.[0-9]+)?)\s*km',r.get('Nota_Validacion') or '') or re.search(r'->\s*([0-9]+(?:\.[0-9]+)?)\s*km',r.get('Nota_Validacion') or '')
        d=float(m.group(1)) if m else None
    return d
ref=collections.defaultdict(list)
for fn,src in [(ROOT+'/experiments/_s143_evaluador/_dl_referencia/92f26b98b490_registro_vrp_consolidado.csv','CONS'),(ROOT+'/experiments/_s143_evaluador/_dl_referencia/f9805ad397dc_registro_vrp_ocr.csv','OCR')]:
    for r in csv.DictReader(open(fn,encoding='utf-8')):
        v=NM.get(norm(r['Volcan'])); 
        if not v or r['Sensor']!='VIIRS375': continue
        t=datetime.strptime(r['Fecha_Satelite_UTC'][:19],'%Y-%m-%d %H:%M:%S')
        if not (W[0]<=t.strftime('%Y-%m-%d')<=W[1]) or t.hour>=12: continue
        ref[v].append(dict(t=t,tipo=r['Tipo_Registro'],vrp=float(r['VRP_MW'] or 0),d=_dist(r,src),src=src))
alert_n={v:{f['t'].strftime('%Y-%m-%d') for f in ref[v] if f['tipo'].startswith('ALERTA')} for v in V}
fp_n={v:{f['t'].strftime('%Y-%m-%d') for f in ref[v] if f['tipo'].startswith('FALSO')} for v in V}
dist_n=collections.defaultdict(list)
for v in V:
    for f in ref[v]:
        if f['tipo'].startswith('ALERTA') and f['d'] is not None: dist_n[(v,f['t'].strftime('%Y-%m-%d'))].append(f['d'])
def pasadas(arm):
    out=[];casos=[]
    for v in V:
        for r in json.load(open(f'{B}/s143ab-{arm}-{v}/{v}.json',encoding='utf-8'))['records']:
            if bp.bucket(r['sensor'])!='VIIRS375': continue
            t=datetime.strptime(r['datetime_utc'],'%Y-%m-%d %H:%M')
            if not (W[0]<=r['datetime_utc'][:10]<=W[1]) or t.hour>=12: continue
            pc=r.get('primary_cluster') or {}
            pos=(pc.get('centroid_lat'),pc.get('centroid_lon')) if pc.get('centroid_lat') is not None else None
            if r.get('final_hotspot_source')=='test1_roi' and r.get('final_hotspot_lat') is not None: pos=(r['final_hotspot_lat'],r['final_hotspot_lon'])
            out.append(dict(v=v,t=t,n=r['datetime_utc'][:10],k=(v,r['datetime_utc'],r['sensor']),pos=pos,src=r.get('final_hotspot_source'),pcd=pc.get('centroid_dist_km'),fhd=r.get('final_hotspot_dist_km'),dc=r.get('distance_class')))
            slim={k:r.get(k) for k in bp.CAMPOS_JS if k!='anomaly_pixels'}
            if r.get('f5_core_vrp_mw') is None: slim['anomaly_pixels']=[{k:p.get(k) for k in ('lat','lon','vrp_mw','bt_k')} for p in (r.get('anomaly_pixels') or [])]
            casos.append([slim,INNER[v]])
    pr=bp.correr_node(casos)
    for p,o in zip(out,pr): p['pub']=o[4]; p['disp']=o[3]; p['art']=o[2]
    for p in out:
        rows=[f for f in ref[p['v']] if abs((f['t']-p['t']).total_seconds())<=120]
        if any(f['tipo'].startswith('ALERTA') for f in rows): p['lab']='pos'
        elif any(f['tipo'].startswith('FALSO') for f in rows): p['lab']='far'
        elif any(f['tipo']=='RUTINA' and f['src']=='CONS' and f['vrp']==0 for f in rows) and p['n'] not in alert_n[p['v']] and p['n'] not in fp_n[p['v']]: p['lab']='neg'
        else: p['lab']='sin'
        p['mir']=[f for f in rows if f['tipo'].startswith('ALERTA') and f['vrp']>0]
    return out
def noches_cota(ps):
    ok={};detalle=collections.defaultdict(list)
    for p in ps:
        if not p['pub'] or p['n'] not in alert_n[p['v']]: continue
        dm=dist_n.get((p['v'],p['n'])) or []
        if p['pos'] is None or not dm: c=None; passes=True
        else:
            c=min(abs(hav(*CEN[p['v']],*p['pos'])-x) for x in dm); passes=c<=0.55
        detalle[(p['v'],p['n'])].append((p['k'][1],p['k'][2],p['src'],round(c,3) if c is not None else None,p['disp'],round(hav(*CEN[p['v']],*p['pos']),2) if p['pos'] else None,p['fhd'],p['pcd']))
        ok.setdefault((p['v'],p['n']),False); ok[(p['v'],p['n'])]|=passes
    return {k for k,x in ok.items() if x}, {k for k in ok}, detalle
R={a:pasadas(a) for a in ARMS}
cc,cpub,cdet=noches_cota(R[ARMS[0]])
print('confirmadas control',len(cc))
neg=[p for p in R[ARMS[0]] if p['lab']=='neg']
print('neg limpio control n',len(neg),'tasa',round(sum(p['pub'] for p in neg)/len(neg),4),'art',sum(p['art'] for p in neg))
json.dump({a:[{**p,'t':str(p['t']),'mir':[{**m,'t':str(m['t'])} for m in p['mir']]} for p in R[a]] for a in ARMS},open('verif/pasadas_'+'_'.join(x[9:] for x in ARMS)+'.json','w'),default=str)
for a in ARMS[1:]:
    bc,bpub,bdet=noches_cota(R[a])
    per=sorted(cc-bc); print(a,'perdidas',len(per),per,'sin filtro',sorted(cc-bpub),'ganancias',len(bc-cc))
    idx={p['k']:p for p in R[a]}
    pares=[(c,idx[c['k']]) for c in neg if c['k'] in idx]
    print('  neg n',len(pares),'tasa brazo',round(sum(b['pub'] for _,b in pares)/len(pares),4),'art brazo',sum(b['art'] for _,b in pares))
    for k in per:
        print('   PERDIDA',k,'dist MIROVA',dist_n.get(k))
        print('     control:',[x for x in cdet[k]])
        print('     brazo  :',[x for x in bdet.get(k,[])])
