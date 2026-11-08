import json,glob,os,sys,io,math,re,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
html=open(r'main\frontend\index.html',encoding='utf8').read()
inner={m.group(1):(float(m.group(2)) if m.group(2) else None) for m in re.finditer(r'name: "(\w+)",[^\n]*?(?:inner_radius_km: ([\d.]+))?,? *(?:vent_radius|hasMirova)',html)}
det=[]
for f in sorted(glob.glob(r'main\data\sombra_34\*.json')):
    v=os.path.basename(f)[:-5]
    for r in json.load(open(f,encoding='utf8'))['records']:
        if (r.get('vrp_mw') or 0)>0: det.append((v,r))
print('inner en frontend de ejemplos',{k:inner.get(k) for k in ['Irruputuncu','Guallatiri','Putana','Lascar']})
def hav(a,b,c,d):
    R=6371;p=math.radians;x=math.sin(p(c-a)/2)**2+math.cos(p(a))*math.cos(p(c))*math.sin(p(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
print('n',len(det),'dist<=5:',sum(r['final_hotspot_dist_km']<=5 for v,r in det),'dist<=10:',sum(r['final_hotspot_dist_km']<=10 for v,r in det))
for v,r in det: print(v,r['datetime_utc'],r['sensor'],round(r['final_hotspot_lat'],3),round(r['final_hotspot_lon'],3),r['final_hotspot_dist_km'],r['vrp_mw'])
print('--- misma pasada y mismo foco (<3 km) entre volcanes')
for i,(v,r) in enumerate(det):
    for w,s in det[i+1:]:
        if r['datetime_utc']==s['datetime_utc'] and r['sensor']==s['sensor']:
            print(v,w,r['datetime_utc'],round(hav(r['final_hotspot_lat'],r['final_hotspot_lon'],s['final_hotspot_lat'],s['final_hotspot_lon']),2),'km')
print('--- repeticion por lugar (<3 km) en distintas noches')
for i,(v,r) in enumerate(det):
    for w,s in det[i+1:]:
        if r['datetime_utc'][:10]!=s['datetime_utc'][:10]:
            d=hav(r['final_hotspot_lat'],r['final_hotspot_lon'],s['final_hotspot_lat'],s['final_hotspot_lon'])
            if d<3: print(v,r['datetime_utc'],w,s['datetime_utc'],round(d,2))
