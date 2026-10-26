# VM m03: la regla (delaunay_perturbado.rellenar, marco fila_col) y el port (griddata/Qhull) contra BK de MATLAB, celda por celda
import sys, numpy as np, collections, json
from pathlib import Path
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
sys.path.insert(0, str(P)); sys.path.insert(0, 'C:/vrp-trabajo/s162-modd/experiments/_s158_audit_r2/oraculo')
import delaunay_perturbado as DP
import mirova_v750_r2 as ORA
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
et = json.loads((P/'entradas_o2_modis_etiquetas.json').read_text(encoding='utf-8'))
K = E['M13'].shape[2]
out = []
for k in range(K):
    m = E['M13'][:,:,k].astype(float)
    a = np.asarray(E['ALERTAS'][k,0]).ravel().astype(int); n=a.size
    mask = np.zeros(m.size, bool); mask[a-1]=True; mask=mask.reshape(m.shape, order='F')
    enm = m.copy(); enm[mask]=np.nan
    ks = 3 if n<=4 else (5 if n<=30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((ks,ks),bool))] = np.nan
    hole = np.isnan(enm)
    BK = R['BK'][k,0]
    Br,_ = DP.rellenar(enm,'xy_fila_col'); Bc,_ = DP.rellenar(enm,'xy_col_fila'); Bp = ORA._fillmissing2_lineal(enm)
    fin = hole & np.isfinite(BK)       # celdas rellenadas por MATLAB
    nanm = hole & np.isnan(BK)
    scale = np.nanmax(m)-np.nanmin(m)
    def d(B, sel): 
        x = np.abs(B[sel]-BK[sel]); return float(x.max()) if x.size else 0.0
    out.append(dict(k=k, npix=n, nhole=int(hole.sum()), nfin=int(fin.sum()), nnan=int(nanm.sum()),
        d_regla_alert=d(Br,mask), d_regla_hole=d(Br,fin), d_col_alert=d(Bc,mask), d_col_hole=d(Bc,fin),
        d_port_alert=d(Bp,mask), d_port_hole=d(Bp,fin), scale=scale,
        regla_vs_port_alert=float(np.abs(Br[mask]-Bp[mask]).max()), regla_vs_col_alert=float(np.abs(Br[mask]-Bc[mask]).max()),
        regla_nan_en_bknan=int(np.isfinite(Br[nanm]).sum())))
json.dump(out, open('m03_regla_vs_bk.json','w'))
import pandas as pd
df = pd.DataFrame(out)
print('escenas', len(df), 'con NaN de MATLAB en el hueco:', int((df.nnan>0).sum()))
for col in ('d_regla_alert','d_regla_hole','d_port_alert','d_port_hole','d_col_alert','d_col_hole'):
    print(col, 'max abs', df[col].max(), '| escenas con dif > 1e-12:', int((df[col]>1e-12).sum()), '> 1e-9:', int((df[col]>1e-9).sum()), '> 1e-6:', int((df[col]>1e-6).sum()))
print('escala radiancia (max-min de la escena): min %.4g mediana %.4g' % (df.scale.min(), df.scale.median()))
print('regla vs port en celdas alerta: escenas con dif > 1e-9:', int((df.regla_vs_port_alert>1e-9).sum()), 'mediana de esa dif relativa a escala:', float((df.regla_vs_port_alert/df.scale).median()))
print('regla vs marco col_fila en alertas: escenas con dif > 1e-9:', int((df.regla_vs_col_alert>1e-9).sum()))
print('por npix:')
for n,g in df.groupby('npix'):
    print(' npix',n,'n',len(g),'| regla==MATLAB alertas(1e-12):',int((g.d_regla_alert<=1e-12).sum()),'| puerto==MATLAB:',int((g.d_port_alert<=1e-12).sum()),'| col==MATLAB:',int((g.d_col_alert<=1e-12).sum()),'| regla==MATLAB en TODO hueco finito:',int((g.d_regla_hole<=1e-12).sum()), '| regla!=port en alertas:', int((g.regla_vs_port_alert>1e-9).sum()))
