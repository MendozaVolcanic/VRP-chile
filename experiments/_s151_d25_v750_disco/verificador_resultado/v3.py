import json,sys,collections,statistics,math
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(sys.argv[1])
s149={tuple(k) for k in json.load(open(sys.argv[2],encoding='utf-8'))['negativos']}
filas=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.rglob('*.json'))]
C1,C2=1.191042e8,1.4387752e4; LAM=4.05
def T(L): return C2/(LAM*math.log(1+C1/(LAM**5*L)))
for clase in ('neg_cero','alerta_cero','control_publica','protegida_publica'):
    sel=[f for f in filas if f['clase']==clase and (clase!='neg_cero' or (f['volcan'],f['pasada_utc'],f['sensor']) in s149)]
    any_pos=0; ratios=[]; frac_pos_scene=[]; pc1=0; pcvrp=[]; pcpix_dT=[]; multi=[]
    for f in sel:
        rec=f['a']['record']; pc=rec.get('primary_cluster') or {}
        c=f['a']['llamadas_fondo'][-1]
        dts=[b-T(Ln) for b,Ln in zip(c['bt_hot_k'],c['L_bg_nuevo'])]
        any_pos+= any(d>0 for d in dts)
        frac_pos_scene.append(sum(d>0 for d in dts)/len(dts))
        # pc pixel: match anomaly_pixels near centroid
        ap=rec.get('anomaly_pixels') or []
        if pc.get('n_pixels')==1:
            pc1+=1
            # closest anomaly pixel to centroid
            best=min(ap,key=lambda p:(p['lat']-pc['centroid_lat'])**2+(p['lon']-pc['centroid_lon'])**2)
            # find its bt in call -> dT
            i=min(range(len(c['bt_hot_k'])),key=lambda i:abs(c['bt_hot_k'][i]-best['bt_k']))
            d=c['bt_hot_k'][i]-T(c['L_bg_nuevo'][i])
            pcpix_dT.append(d)
            if d>0.05: ratios.append(pc['vrp_mw']/d)
        else: multi.append((pc.get('n_pixels'),pc.get('vrp_mw')))
        pcvrp.append(pc.get('vrp_mw') or 0)
    m=lambda xs: round(statistics.median(xs),3) if xs else None
    print(clase,len(sel),'pasadas con algun pixel >0:',any_pos,' frac pix>0 por pasada mediana',m(frac_pos_scene),
          ' pc 1px',pc1,' dT pc1px mediana',m(pcpix_dT),'min',round(min(pcpix_dT),3) if pcpix_dT else None,
          ' MW/K',m(ratios),' pc vrp mediana',m(pcvrp),' multi',len(multi), 'multi vrp med', m([v for _,v in multi]))
