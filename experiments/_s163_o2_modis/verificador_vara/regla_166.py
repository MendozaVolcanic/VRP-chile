import sys, numpy as np, collections
from scipy.io import loadmat
sys.path.insert(0,'copia'); import delaunay_perturbado as DP
sys.stdout.reconfigure(encoding='utf-8')
V=loadmat('viirs_matlab/entradas_o2.mat'); R=loadmat('viirs_matlab/resultado_o2.mat')
def hueco(M,idx):
    n,m=M.shape; flat=M.reshape(-1,order='F').copy(); flat[idx]=np.nan; X=flat.reshape((n,m),order='F')
    npix=len(idx); k=3 if npix<=4 else (5 if npix<=30 else 7); r=k//2
    nan=np.isnan(X); out=np.zeros_like(nan)
    for i in range(n):
        for j in range(m):
            if nan[max(0,i-r):i+r+1,max(0,j-r):j+r+1].any(): out[i,j]=True
    Y=X.copy(); Y[out]=np.nan; return Y
res=collections.defaultdict(lambda:[0,0,0,0]); nodisc=0
formas=collections.Counter()
for i in range(311):
    a=np.asarray(R['ALERTAS'][i,0]).ravel(); BK=R['BK'][i,0]
    if len(a)==0 or BK.shape!=(67,67): continue
    M=V['M13'][:,:,i]; idx=a.astype(int)-1; Y=hueco(M,idx)
    B1,_=DP.rellenar(Y,'xy_fila_col'); B2,_=DP.rellenar(Y,'xy_col_fila')
    h=np.isnan(Y)
    ok1=np.nanmax(np.abs(BK[h]-B1[h]))<=1e-9*max(1,np.nanmax(np.abs(BK[h])))
    ok2=np.nanmax(np.abs(BK[h]-B2[h]))<=1e-9*max(1,np.nanmax(np.abs(BK[h])))
    clase='1-4' if len(a)<=4 else ('5-30' if len(a)<=30 else '31+')
    res[clase][0]+=1; res[clase][1]+=ok1; res[clase][2]+=ok2; res[clase][3]+= int(np.isnan(M).any())
    if len(a)<=4:
        f=idx%67; c=idx//67; formas[tuple(sorted(zip((f-f.min()).tolist(),(c-c.min()).tolist())))]+=1
tot=sum(v[0] for v in res.values())
print('escenas VIIRS con BK de MATLAB:',tot)
for k,v in res.items(): print(' npix',k,'n',v[0],'regla coincide con BK en todo el hueco:',v[1],'| marco cambiado coincide:',v[2],'| con NaN orig:',v[3])
print('formas 1-4 en VIIRS:',dict(formas))
