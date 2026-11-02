import json,yaml,statistics as st
by=json.load(open('byv.json'))
d=yaml.safe_load(open('volcanoes.yaml',encoding='utf-8'))
vv=d['volcanoes'] if isinstance(d,dict) else d
lat={x['name']:x['lat'] for x in vv}
xs=[];ys=[]
for v,x in by.items():
    pipe=[p for p in x['pipe'] if p>0]
    xs.append(abs(lat[v])); ys.append(st.median(pipe))
n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
b=sum((a-mx)*(c-my) for a,c in zip(xs,ys))/sum((a-mx)**2 for a in xs); a0=my-b*mx
r=sum((a-mx)*(c-my) for a,c in zip(xs,ys))/(sum((a-mx)**2 for a in xs)*sum((c-my)**2 for c in ys))**.5
print('slope min/deg %.3f intercept %.2f r %.2f n %d'%(b,a0,r,n))
tot=0
for x in vv:
    if x['name'] in by: continue
    pred=a0+b*abs(x['lat']); tot+=pred
    print(x['name'],x['lat'],round(pred,1),end=' | ')
print(); print('mean pred 34: %.1f'%(tot/34))
