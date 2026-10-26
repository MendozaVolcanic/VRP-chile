# Verificador: la regla (xy_fila_col) contra el BK que MATLAB devolvio en VIIRS 750, hueco reimplementado a mano desde el .m
import sys, json, numpy as np
from scipy.io import loadmat
sys.path.insert(0,'copia')
import delaunay_perturbado as DP
sys.stdout.reconfigure(encoding='utf-8')
E=loadmat('viirs_matlab/entradas_o2.mat'); R=loadmat('viirs_matlab/resultado_o2.mat')
K=E['M13'].shape[2]

def mi_hueco(M, lin):
    """Reimplementacion propia del .m: indices lineales MATLAB (col primero, base 1), imdilate cuadrado por bucle."""
    n,m=M.shape
    X=M.copy()
    flat=X.reshape(-1,order='F')       # vista col-primero
    idx=np.asarray(lin).ravel().astype(int)-1
    flat[idx]=np.nan
    X=flat.reshape((n,m),order='F')
    npix=len(idx)
    k=3 if npix<=4 else (5 if npix<=30 else 7)
    r=k//2
    nan=np.isnan(X)
    out=np.zeros_like(nan)
    for i in range(n):
        for j in range(m):
            if nan[max(0,i-r):i+r+1, max(0,j-r):j+r+1].any(): out[i,j]=True
    Y=X.copy(); Y[out]=np.nan
    return Y, idx

res=[]
for i in range(K):
    M=E['M13'][:,:,i]; a=np.asarray(R['ALERTAS'][i,0]).ravel()
    n=len(a)
    if n<1 or n>4 or R["BK"][i,0].shape!=M.shape: continue
    Y,idx=mi_hueco(M,a)
    BK=R['BK'][i,0]
    fila=[]
    B1,_=DP.rellenar(Y,'xy_fila_col')
    B2,_=DP.rellenar(Y,'xy_col_fila')
    # la matriz BK de MATLAB coincide con los valores conocidos fuera del hueco?
    ok=np.isfinite(Y)
    asigna=np.nanmax(np.abs(BK[ok]-Y[ok])) if ok.any() else np.nan
    mask=np.zeros(M.size,bool); mask[idx]=True; mask=mask.reshape(M.shape,order='F')
    # delta de L: lo que importa (suma del fondo sobre alertas)
    lbk_m=float(R['LBK'][i,0]); lbk_1=float(np.nansum(B1[mask])); lbk_2=float(np.nansum(B2[mask]))
    # el hueco de MATLAB: celdas de BK que no estan en Y pero estan finitas -> relleno; comparar completo en el hueco
    h=~ok
    e1=np.nanmax(np.abs(BK[h]-B1[h])) if h.any() else 0.0
    e2=np.nanmax(np.abs(BK[h]-B2[h])) if h.any() else 0.0
    res.append(dict(i=i,n=n,fam=json.load(open('viirs_matlab/entradas_o2_etiquetas.json',encoding='utf-8'))[i]['familia'] if False else '',
        asigna=float(asigna),e_regla=float(e1),e_cambiado=float(e2),lbk_m=lbk_m,lbk_1=lbk_1,lbk_2=lbk_2,nhole=int(h.sum()),nanorig=int(np.isnan(M).sum())))
import collections
for n in (1,2,3,4):
    g=[r for r in res if r['n']==n]
    if not g: continue
    print('npix',n,'escenas',len(g),
          '| BK de MATLAB == valores conocidos fuera del hueco (max |dif|<=1e-12):',sum(r['asigna']<=1e-12 for r in g),
          '| hueco propio coincide en forma con celdas NaN del Y',  '' )
    print('   regla xy_fila_col: BK completo en el hueco igual a 1e-9:',sum(r['e_regla']<=1e-9*max(1,1) for r in g),
          '| marco cambiado igual:',sum(r['e_cambiado']<=1e-9 for r in g),
          '| LBK regla igual a 1e-12 rel:',sum(abs(r['lbk_1']-r['lbk_m'])<=1e-12*max(1,abs(r['lbk_m'])) for r in g),
          '| LBK cambiado:',sum(abs(r['lbk_2']-r['lbk_m'])<=1e-12*max(1,abs(r['lbk_m'])) for r in g))
print('con NaN originales en M13:',sum(r['nanorig']>0 for r in res),'de',len(res))
print('max |BK-Y| fuera del hueco:',max(r['asigna'] for r in res))
json.dump(res,open('regla_vs_matlab_viirs.json','w'),indent=1)
