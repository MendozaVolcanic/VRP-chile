import sys, numpy as np, collections, json
from scipy.io import loadmat
sys.path.insert(0,'copia'); import delaunay_perturbado as DP
sys.stdout.reconfigure(encoding='utf-8')
V=loadmat('viirs_matlab/entradas_o2.mat'); R=loadmat('viirs_matlab/resultado_o2.mat')
et=json.load(open('viirs_matlab/entradas_o2_etiquetas.json',encoding='utf-8'))
def hueco(M,idx):
    n,m=M.shape; flat=M.reshape(-1,order='F').copy(); flat[idx]=np.nan; X=flat.reshape((n,m),order='F')
    npix=len(idx); k=3 if npix<=4 else (5 if npix<=30 else 7); r=k//2
    nan=np.isnan(X); out=np.zeros_like(nan)
    for i in range(n):
        for j in range(m):
            if nan[max(0,i-r):i+r+1,max(0,j-r):j+r+1].any(): out[i,j]=True
    Y=X.copy(); Y[out]=np.nan; return Y
res=collections.defaultdict(lambda:[0,0,0,0]); fam=collections.Counter()
for i in range(311):
    a=np.asarray(R['ALERTAS'][i,0]).ravel()
    if len(a)==0: continue
    M=V['M13'][:,:,i]; idx=a.astype(int)-1; Y=hueco(M,idx)
    mask=np.zeros(M.size,bool); mask[idx]=True; mask=mask.reshape(M.shape,order='F')
    lbk_m=float(R['LBK'][i,0])
    B1,_=DP.rellenar(Y,'xy_fila_col'); B2,_=DP.rellenar(Y,'xy_col_fila')
    ok1=abs(float(np.nansum(B1[mask]))-lbk_m)<=1e-9*abs(lbk_m); ok2=abs(float(np.nansum(B2[mask]))-lbk_m)<=1e-9*abs(lbk_m)
    clase='1-4' if len(a)<=4 else ('5-30' if len(a)<=30 else '31+')
    res[clase][0]+=1; res[clase][1]+=ok1; res[clase][2]+=ok2; res[clase][3]+=int(np.isnan(M).any())
    fam[(et[i]['familia'], clase)]+=1
print('escenas con alertas:',sum(v[0] for v in res.values()))
for k,v in res.items(): print(' npix',k,'n',v[0],'LBK regla == LBK MATLAB (1e-9 rel):',v[1],'| marco cambiado:',v[2],'| con NaN orig en M13:',v[3])
print(dict(fam)); print('version',R['version_matlab'])
