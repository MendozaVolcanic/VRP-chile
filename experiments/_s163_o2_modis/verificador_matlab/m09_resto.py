import sys, json, hashlib, numpy as np, pandas as pd
from pathlib import Path
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
sys.path.insert(0, str(P))
import delaunay_perturbado as DP
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
df = pd.read_json('m06_por_forma.json')
# 1) 1 pixel: ruido del port vs MATLAB
x = df[df.forma=='1']
r = (x.vrp_port/x.vrp_mat)
print('1 px filas: mediana |rel| %.4f; ratio mediana %.4f, media %.4f; ratio>1: %d, <1: %d, =1(1e-6): %d' % (x.rel.abs().median(), r.median(), r.mean(), (r>1+1e-6).sum(), (r<1-1e-6).sum(), (abs(r-1)<=1e-6).sum()))
xd = x.drop_duplicates('h'); rd = xd.vrp_port/xd.vrp_mat
print('1 px distintas: mediana |rel| %.4f ; con dif: mediana |rel| %.4f' % (xd.rel.abs().median(), xd.rel[xd.rel.abs()>1e-6].abs().median()))
y = df[df.forma=='2x2'].drop_duplicates('h'); print('2x2 distintas |rel| port vs MATLAB:', np.round(y.rel.values,4).tolist())
# Llaima
for k in range(404):
    if abs(df.vrp_mat[k]-0.1140)<5e-4 and df.vrp_port[k]>0.43: print('Llaima-like k',k,df.vrp_mat[k],df.vrp_port[k]); break
# 2) celdas del hueco donde MATLAB deja NaN aunque M13 era finito, y que hace la regla
tot=0; esc=0; alertas_nan=0
for k in range(404):
    m=E['M13'][:,:,k].astype(float); BK=R['BK'][k,0]
    nn = np.isnan(BK)&np.isfinite(m)
    if nn.any(): esc+=1; tot+=int(nn.sum())
print('escenas con celdas NaN en BK que eran finitas en M13:', esc, 'celdas:', tot)
# 3) igualdad exacta bit a bit de regla vs BK (independencia aritmetica)
exact=0; n=0
for k in (0,86,205,300,386):
    m=E['M13'][:,:,k].astype(float); a=np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)
    mask=np.zeros(m.size,bool); mask[a-1]=True; mask=mask.reshape(m.shape,order='F')
    enm=m.copy(); enm[mask]=np.nan; ks=3
    enm[binary_dilation(np.isnan(enm),structure=np.ones((ks,ks),bool))]=np.nan
    B,_=DP.rellenar(enm,'xy_fila_col'); BK=R['BK'][k,0]; s=np.isnan(enm)&np.isfinite(BK)
    exact+=int((B[s]==BK[s]).sum()); n+=int(s.sum())
print('celdas del hueco con igualdad bit a bit regla==MATLAB en 5 escenas:', exact, 'de', n)
