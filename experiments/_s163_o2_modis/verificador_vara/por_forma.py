import sys, json, collections, numpy as np
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8'))
J=json.load(open('../vara_preliminar_fillmissing2.json',encoding='utf-8')); sig=json.load(open('firmas.json'))['sig']
R=loadmat('viirs_matlab/resultado_o2.mat')
def forma(a,n):
    f=a%n; c=a//n; return tuple(sorted(zip((f-f.min()).tolist(),(c-c.min()).tolist())))
fv=collections.Counter()
for i in range(311):
    a=np.asarray(R['ALERTAS'][i,0]).ravel().astype(int)-1
    if 1<=len(a)<=4: fv[forma(a,67)]+=1
g=collections.defaultdict(list)
for i in range(len(et)):
    a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1; g[forma(a,51)].append(i)
print('forma | npix | filas | distintas | filas con |dif|>1% | distintas con >1% | n escenas VIIRS (MATLAB) con esa forma')
for fo,L in sorted(g.items(),key=lambda t:(len(t[0]),-len(t[1]))):
    r=np.array([J[i]['vrp_port_recalculado_mw']/J[i]['vrp_regla_matlab_mw'] for i in L])
    d=len({sig[i] for i in L}); dd=len({sig[i] for i,x in zip(L,r) if abs(x-1)>.01})
    print(fo,len(fo),len(L),d,int((abs(r-1)>.01).sum()),dd,fv.get(fo,0))
