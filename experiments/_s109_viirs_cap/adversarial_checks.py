"""S109 adversarial checks (A62) for VIIRS-cap-of-MODIS candidate (b).
1. Of MODIS-inflated nights: how many have NO VIIRS PASS AT ALL same night
   (any VIIRS record, detected or not) -> nights where a VIIRS cap is UNAVAILABLE.
2. Compare our VIIRS magnitude vs MIROVA's own VIIRS375 VRP_MW on the same night
   (does our VIIRS approximate the published truth?).
3. Check whether "summit" via cluster_dist disagrees with distance_class (A46 trap).
"""
import json, csv, collections, datetime, statistics, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
VOLS = ['Chaiten','Villarrica','Llaima','Tupungatito','PuyehueCordonCaulle']
INNER = {'Chaiten':5,'Villarrica':5,'Llaima':5,'Tupungatito':7,'PuyehueCordonCaulle':20}
WINDOW_H = 12.0
MODIS_THRESH = 5.0
def pdt(s): return datetime.datetime.strptime(s,"%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc)
def is_modis(s): return s.startswith('MODIS')
def is_viirs(s): return s.startswith('VIIRS')
def is_viirs375(s): return s.startswith('VIIRS') and not s.endswith('_750')
def pcvrp(r): return (r.get('primary_cluster') or {}).get('vrp_mw',0) or 0
def pcdist(r): return (r.get('primary_cluster') or {}).get('centroid_dist_km',None)
def load(v): return json.load(open(os.path.join(ROOT,'data','mirova_equivalent',v+'.json')))['records']

print("="*70); print("CHECK 1: VIIRS PASS availability on MODIS-inflated nights"); print("="*70)
for v in VOLS:
    recs=load(v); inner=INNER[v]
    modis_hi=[r for r in recs if is_modis(r['sensor']) and pcvrp(r)>MODIS_THRESH and (pcdist(r) or 1e9)<=inner]
    viirs_all=[(pdt(r['datetime_utc']),r) for r in recs if is_viirs(r['sensor'])]
    no_pass=0
    for r in modis_hi:
        t0=pdt(r['datetime_utc'])
        if not any(abs((vt-t0).total_seconds())/3600<=WINDOW_H for vt,_ in viirs_all):
            no_pass+=1
    n=len(modis_hi)
    print(f"{v}: {no_pass}/{n} MODIS-inflated nights have NO VIIRS pass at all (+/-{WINDOW_H}h)")

print("\n"+"="*70); print("CHECK 2: our VIIRS vs MIROVA VIIRS375 published VRP, same night"); print("="*70)
csv_path=os.path.join(ROOT,'latest_consolidado.csv')
ALIASES={'Chaiten':{'Chaiten','Chaitén'},'Villarrica':{'Villarrica'},'Llaima':{'Llaima'},
 'Tupungatito':{'Tupungatito'},'PuyehueCordonCaulle':{'PuyehueCordonCaulle','Puyehue-Cordon Caulle','Puyehue','Cordon Caulle'}}
rows=list(csv.DictReader(open(csv_path,encoding='utf-8-sig')))
def csv_dt(s):
    try: return datetime.datetime.strptime(s,"%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except: return datetime.datetime.strptime(s,"%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc)
for v in VOLS:
    recs=load(v); inner=INNER[v]
    # our viirs summit records
    our=[(pdt(r['datetime_utc']),pcvrp(r),r['sensor']) for r in recs
         if is_viirs(r['sensor']) and pcvrp(r)>0 and (pcdist(r) or 1e9)<=inner]
    # mirova viirs375 ALERTA rows with VRP
    mrows=[r for r in rows if r['Volcan'] in ALIASES[v] and r['Sensor']=='VIIRS375'
           and 'ALERTA' in (r['Tipo_Registro'] or '').upper()]
    pairs=[]
    for mr in mrows:
        try: mvrp=float(mr['VRP_MW'])
        except: continue
        if mvrp<=0: continue
        mt=csv_dt(mr['Fecha_Satelite_UTC'])
        cands=[(ov, os_) for (ot,ov,os_) in our if abs((ot-mt).total_seconds())/3600<=WINDOW_H]
        if cands:
            ours=max(c[0] for c in cands)  # our best viirs that night
            pairs.append((mvrp, ours))
    if pairs:
        ratios=[o/m for m,o in pairs if m>0]
        print(f"{v}: matched {len(pairs)} MIROVA-VIIRS375 ALERTA nights to our VIIRS")
        print(f"   MIROVA VRP median={statistics.median([m for m,_ in pairs]):.2f}MW  "
              f"our VIIRS median={statistics.median([o for _,o in pairs]):.2f}MW  "
              f"our/MIROVA median ratio={statistics.median(ratios):.2f}x")
    else:
        print(f"{v}: 0 matched MIROVA-VIIRS375 ALERTA nights (mrows={len(mrows)})")

print("\n"+"="*70); print("CHECK 3: distance_class vs cluster_dist on MODIS-inflated (A46 trap)"); print("="*70)
for v in VOLS:
    recs=load(v); inner=INNER[v]
    modis_hi=[r for r in recs if is_modis(r['sensor']) and pcvrp(r)>MODIS_THRESH and (pcdist(r) or 1e9)<=inner]
    dc=collections.Counter(r.get('distance_class') for r in modis_hi)
    print(f"{v}: of {len(modis_hi)} cluster-summit MODIS-inflated, distance_class={dict(dc)}")
