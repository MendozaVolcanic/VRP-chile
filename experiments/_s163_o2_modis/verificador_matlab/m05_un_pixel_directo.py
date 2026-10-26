# VM m05: sin la regla. En alertas de 1 pixel, que par promedia MATLAB en el centro? (de BK de MATLAB, M13 de entradas)
import sys, numpy as np, collections, json
from pathlib import Path
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
c = collections.Counter(); ejemplos=[]
for k in range(E['M13'].shape[2]):
    a = np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)
    if a.size!=1: continue
    f=(a[0]-1)%51; col=(a[0]-1)//51; M=E['M13'][:,:,k].astype(float); BK=R['BK'][k,0]
    cands = {'fila(f-2,f+2)':(M[f-2,col]+M[f+2,col])/2 if 2<=f<=48 else np.nan,
             'col(c-2,c+2)':(M[f,col-2]+M[f,col+2])/2 if 2<=col<=48 else np.nan}
    t = BK[f,col]
    hit = [n for n,v in cands.items() if np.isfinite(v) and abs(t-v)<=1e-12*abs(v)]
    dif = np.isfinite(cands['fila(f-2,f+2)']) and np.isfinite(cands['col(c-2,c+2)']) and abs(cands['fila(f-2,f+2)']-cands['col(c-2,c+2)'])>1e-12
    c[(tuple(hit), 'pares_distintos' if dif else 'pares_iguales/NaN')]+=1
    if not hit: ejemplos.append((k,f,col,t,cands))
for kk,v in sorted(c.items(), key=lambda x:-x[1]): print(kk,v)
print('sin acierto:', ejemplos[:5])
