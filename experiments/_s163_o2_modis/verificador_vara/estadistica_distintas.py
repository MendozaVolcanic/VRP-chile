import sys, json, collections, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
J=json.load(open('../vara_preliminar_fillmissing2.json',encoding='utf-8'))
sig=json.load(open('firmas.json'))['sig']
r=np.array([j['vrp_port_recalculado_mw']/j['vrp_regla_matlab_mw'] for j in J])
vp=np.array([j['vrp_port_recalculado_mw'] for j in J]); vr=np.array([j['vrp_regla_matlab_mw'] for j in J])
print('VRP regla <=0:',int((vr<=0).sum()),'| VRP port <=0:',int((vp<=0).sum()),'| min regla',vr.min(),'min port',vp.min(),'| no finitos',int((~np.isfinite(r)).sum()))
# recomputar cifras de la salida
for n in (1,2,3,4):
    s=np.array([j['npix']==n for j in J]); x=r[s]
    print('FILAS npix',n,'n',s.sum(),'mediana',round(float(np.median(x)),4),'mediana |r-1|',round(float(np.median(np.abs(x-1))),4),
          '|dif|>1%',int((abs(x-1)>.01).sum()),'>10%',int((abs(x-1)>.1).sum()),'iguales 1e-9',int((abs(x-1)<=1e-9).sum()),
          'ratio<1:',int((x<1-1e-9).sum()),'ratio>1:',int((x>1+1e-9).sum()))
# distintas: una por firma (la ratio es identica entre filas de la misma firma salvo el coeficiente, que se cancela)
vistos={}; 
for i,s in enumerate(sig):
    if s not in vistos: vistos[s]=i
ids=sorted(vistos.values())
print('\nESCENAS DISTINTAS (grilla+mascara), n',len(ids))
# verifica que filas con la misma firma den la misma ratio
inc=0
g=collections.defaultdict(list)
for i,s in enumerate(sig): g[s].append(i)
for s,L in g.items():
    if len(L)>1 and (max(r[L])-min(r[L]))>1e-9: inc+=1
print('firmas repetidas con ratio distinta entre filas:',inc)
for n in (1,2,3,4):
    s=[i for i in ids if J[i]['npix']==n]; x=r[s]
    print('  npix',n,'n',len(s),'mediana',round(float(np.median(x)),4),'p5 %.4f p95 %.4f'%(np.percentile(x,5),np.percentile(x,95)),'mediana|r-1| %.4f'%np.median(np.abs(x-1)),
          '|dif|>1%',int((abs(x-1)>.01).sum()),'>10%',int((abs(x-1)>.1).sum()),'iguales',int((abs(x-1)<=1e-9).sum()))
# solo fisica
print('\nvariante fisica (filas), n por npix:',{n:sum(1 for j in J if j['variante']=='fisica' and j['npix']==n) for n in (1,2,3,4)})
ids_f=[i for i in ids if J[i]['variante']=='fisica']
print('  firmas distintas dentro de fisica:',len({sig[i] for i in range(len(J)) if J[i]['variante']=='fisica'}))
# pasadas por volcan
c=collections.Counter(j['volcan'] for j in J); print('filas por volcan',dict(c))
cd=collections.Counter(J[i]['volcan'] for i in ids); print('distintas por volcan',dict(cd))
# 1 pixel >10% por volcan (distintas)
for v in sorted(cd):
    s=[i for i in ids if J[i]['volcan']==v and J[i]['npix']==1]
    if s: print('  1px',v,'n',len(s),'mediana|r-1| %.3f'%np.median(np.abs(r[s]-1)),'>10%:',int((abs(r[s]-1)>.1).sum()))
# la frase de la escena Llaima x3.777: cuantas filas / distintas
idx=[i for i in range(len(J)) if abs(r[i]-3.777)<0.01]; print('filas con ratio ~3.777:',len(idx),'firmas',len({sig[i] for i in idx}))
# la escena 'otro' (1 pixel donde port no es ni fila ni col)
