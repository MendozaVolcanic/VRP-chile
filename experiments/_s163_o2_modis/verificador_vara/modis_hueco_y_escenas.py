# Verificador: (1) hueco MODIS reimplementado a mano vs el del script; (2) escenas distintas por npix; (3) borde; (4) NaN
import sys, json, hashlib, collections, numpy as np
from scipy.io import loadmat
sys.path.insert(0,'copia'); sys.path.insert(0,'..')
sys.stdout.reconfigure(encoding='utf-8')
E=loadmat('../entradas_o2_modis.mat'); et=json.load(open('../entradas_o2_modis_etiquetas.json',encoding='utf-8'))
J=json.load(open('../vara_preliminar_fillmissing2.json',encoding='utf-8'))
K=len(et); print('K',K, E['M13'].shape, E['M13'].dtype)
import importlib.util
spec=importlib.util.spec_from_file_location('vp','copia/vara_preliminar_fillmissing2.py'); vp=importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)

def mi_hueco(M, lin):
    n,m=M.shape
    flat=M.reshape(-1,order='F').copy()
    idx=np.asarray(lin).ravel().astype(int)-1
    assert len(set(idx))==len(idx)
    flat[idx]=np.nan
    X=flat.reshape((n,m),order='F')
    npix=len(idx); k=3 if npix<=4 else (5 if npix<=30 else 7); r=k//2
    nan=np.isnan(X); out=np.zeros_like(nan)
    for i in range(n):
        for j in range(m):
            if nan[max(0,i-r):i+r+1, max(0,j-r):j+r+1].any(): out[i,j]=True
    Y=X.copy(); Y[out]=np.nan
    mask=np.zeros(M.size,bool); mask[idx]=True
    return Y, mask.reshape((n,m),order='F'), idx

dif_hueco=0; nan_orig=0; npix_ok=0; minborde=[]; sig=[]
for i in range(K):
    M=E['M13'][:,:,i].astype(float); a=np.asarray(E['ALERTAS'][i,0]).ravel()
    Y,mask,idx=mi_hueco(M,a)
    # el del script
    m2=np.zeros(M.shape,bool); m2[np.unravel_index(a.astype(int)-1,M.shape,order='F')]=True
    Ys=vp.hueco(M,m2)
    if not np.array_equal(np.isnan(Y),np.isnan(Ys)) or not np.array_equal(mask,m2): dif_hueco+=1
    nan_orig+= int(np.isnan(M).sum()>0)
    npix_ok+= int(mask.sum()==et[i]['npix'])
    f,c=np.nonzero(mask); n=M.shape[0]
    minborde.append(int(min(f.min(),c.min(),n-1-f.max(),n-1-c.max())))
    sig.append(hashlib.md5(M.tobytes()+mask.tobytes()).hexdigest())
print('hueco propio != hueco del script en',dif_hueco,'de',K)
print('escenas con NaN en la grilla original:',nan_orig,'| npix de la etiqueta == mascara:',npix_ok)
print('distancia minima de las alertas al borde (celdas): min',min(minborde),'conteo por valor <=5:',dict(sorted(collections.Counter(v for v in minborde if v<=5).items())))
# escenas distintas
d=collections.defaultdict(list)
for i,s in enumerate(sig): d[s].append(i)
print('escenas distintas (grilla+mascara identicas colapsadas):',len(d),'de',K)
for n in (1,2,3,4):
    tot=sum(1 for e in et if e['npix']==n); dist=len({sig[i] for i,e in enumerate(et) if e['npix']==n})
    print('  npix',n,'filas',tot,'distintas',dist)
# repetidas por (volcan,hora,variante) entre lotes
c=collections.Counter((e['volcan'],e['hora_utc'],e['variante']) for e in et)
print('claves (volcan,hora,variante) repetidas:',sum(1 for v in c.values() if v>1))
c2=collections.Counter((e['lote'],e['id']) for e in et); print('pasadas (lote,id):',len(c2))
c3=collections.Counter((e['volcan'],e['hora_utc']) for e in et); print('pasadas (volcan,hora):',len(c3))
# mismo (volcan,hora) en dos lotes?
l=collections.defaultdict(set)
for e in et: l[(e['volcan'],e['hora_utc'])].add(e['lote'])
print('pasadas (volcan,hora) en ambos lotes:',sum(1 for v in l.values() if len(v)>1))
json.dump({'sig':sig},open('firmas.json','w'))
