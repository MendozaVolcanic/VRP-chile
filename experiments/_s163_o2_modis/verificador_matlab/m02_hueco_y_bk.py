# VM m02: reconstruye el hueco desde el .m, comprueba que BK de MATLAB es M13 fuera del hueco, y mira NaN en BK
import sys, numpy as np, collections
from pathlib import Path
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
K = E['M13'].shape[2]
c = collections.Counter(); naninalert = []; nanhole = []
lbk_ok = 0; dl_ok = 0
for k in range(K):
    m = E['M13'][:,:,k].astype(float)
    a = np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)
    n = a.size
    mask = np.zeros(m.size, bool); mask[a-1] = True; mask = mask.reshape(m.shape, order='F')
    enm = m.copy(); enm[mask] = np.nan
    ks = 3 if n <= 4 else (5 if n <= 30 else 7)
    hueco = binary_dilation(np.isnan(enm), structure=np.ones((ks,ks), bool))   # imdilate(isnan, strel square ks), borde: fuera = 0
    BK = R['BK'][k,0]
    fuera = ~hueco
    # fuera del hueco BK debe ser exactamente M13 (donde M13 es finito)
    ok_f = np.array_equal(BK[fuera], m[fuera], equal_nan=True)
    c['BK==M13 fuera del hueco (incluye NaN igual)'] += ok_f
    # celdas que cambian respecto de M13 por estar en el hueco
    camb = np.isfinite(BK) & ~(BK == m)
    c['celdas cambiadas subconjunto del hueco'] += bool(np.all(hueco[camb]))
    # NaN en BK
    nn = np.isnan(BK)
    c['escenas con NaN en BK'] += bool(nn.any())
    c['NaN de BK dentro de hueco'] += int((nn & hueco).sum()); c['NaN de BK fuera del hueco'] += int((nn & ~hueco).sum())
    if (nn & mask).any(): naninalert.append((k, int((nn&mask).sum())))
    if (np.isnan(m) & ~mask).any(): c['escenas con NaN original (no alerta) en M13'] += 1
    # LBK y DL recomputados
    lbk = np.nansum(BK[mask]); lh = np.nansum(m[mask])
    lbk_ok += abs(lbk - float(R['LBK'][k,0]))<=1e-12*max(1,abs(lbk)) if R['LBK'].ndim>1 else abs(lbk - float(R['LBK'][k]))<=1e-12*max(1,abs(lbk))
    dl = float(R['DL'][k,0]) if R['DL'].ndim>1 else float(R['DL'][k])
    dl_ok += abs((lh-lbk)-dl) <= 1e-12*max(1,abs(dl))
    # alertas con valores finitos?
    c['alertas con M13 NaN'] += int(np.isnan(m[mask]).sum())
for kk,v in c.items(): print(kk, v)
print('LBK recomputado == LBK mat:', lbk_ok, 'de', K, '| DL == LHOT-LBK:', dl_ok, 'de', K)
print('escenas con NaN de BK en celdas de alerta:', len(naninalert), naninalert[:10])
