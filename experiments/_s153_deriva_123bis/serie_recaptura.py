# Serie mensual (por mes de OBSERVACION) de la recaptura del segundo pase en HEAD, por familia de sensor.
import json,sys,io,collections,statistics as st
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
R="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent/"
V=['Chaiten','Copahue','Isluga','Lascar','Lastarria','Llaima','NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito','Villarrica']
acc=collections.defaultdict(list)
for v in V:
    x=json.load(open(R+v+'.json',encoding='utf-8')); x=x['records'] if isinstance(x,dict) else x
    for r in x:
        s=r['sensor']; fam='MODIS' if s.startswith('MODIS') else ('V750' if s.endswith('_750') else 'V375')
        if not (r.get('n_anomalous_pixels') or 0): continue
        sp=r.get('diag_n_second_pass_recapture'); n=r.get('n_anomalous_pixels')
        if sp is None: continue
        acc[(fam,r['datetime_utc'][:7],v=='Villarrica')].append((sp,n))
for fam in ['MODIS','V375','V750']:
    print(fam,'mes | n | mediana recaptura | fraccion recaptura/total (no Villarrica)')
    for m in sorted({k[1] for k in acc if k[0]==fam}):
        L=acc.get((fam,m,False),[])
        if len(L)<20 or m<'2025-01': continue
        print(' ',m,len(L),st.median(a for a,b in L),round(sum(a for a,b in L)/max(1,sum(b for a,b in L)),3))
