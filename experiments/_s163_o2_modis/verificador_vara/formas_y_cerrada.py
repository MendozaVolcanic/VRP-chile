import sys, json, collections, numpy as np
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
def forma(lin,n):
    idx=np.asarray(lin).ravel().astype(int)-1
    f=idx%n; c=idx//n
    pts=sorted(zip(f.tolist(),c.tolist()))
    f0=min(p[0] for p in pts); c0=min(p[1] for p in pts)
    return tuple((p[0]-f0,p[1]-c0) for p in pts)
V=loadmat('viirs_matlab/entradas_o2.mat'); R=loadmat('viirs_matlab/resultado_o2.mat')
formasV=collections.Counter()
for i in range(311):
    a=np.asarray(R['ALERTAS'][i,0]).ravel()
    if 1<=len(a)<=4: formasV[forma(a,67)]+=1
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8'))
sig=json.load(open('firmas.json'))['sig']
formasM=collections.Counter(); filas=[]
for i,e in enumerate(et):
    a=np.asarray(E['ALERTAS'][i,0]).ravel(); fo=forma(a,51); formasM[fo]+=1
    filas.append((i,fo))
print('formas (traslacion) VIIRS validadas con LBK de MATLAB (todas las de 1-4 pix):',len(formasV),'| escenas',sum(formasV.values()))
print('formas MODIS:',len(formasM))
nov=[i for i,fo in filas if fo not in formasV]
print('escenas MODIS (filas) con forma NO vista en las 147 de 1-4 pix de VIIRS:',len(nov),'de',len(et))
print('  distintas:',len({sig[i] for i in nov}))
for n in (1,2,3,4):
    fm=[fo for fo in formasM if len(fo)==n]; nv=[fo for fo in fm if fo not in formasV]
    print('  npix',n,'formas MODIS',len(fm),'no vistas en VIIRS',len(nv),'filas MODIS en no vistas',sum(formasM[fo] for fo in nv))
print('las formas no vistas de 2..4 pix:'); 
for fo in formasM:
    if fo not in formasV and len(fo)>1: print('  ',fo,formasM[fo])
# NaN originales en MODIS: donde
for i in range(len(et)):
    M=E['M13'][:,:,i]
    if np.isnan(M).any():
        f,c=np.nonzero(np.isnan(M)); a=np.asarray(E['ALERTAS'][i,0]).ravel().astype(int)-1
        af=a%51; ac=a//51
        d=min(max(abs(int(x)-int(y)),abs(int(u)-int(v))) for x,u in zip(f,c) for y,v in zip(af,ac))
        print('NaN orig escena',i,et[i]['volcan'],et[i]['variante'],'nNaN',len(f),'dist Chebyshev a la alerta',d)
