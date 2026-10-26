# VM m01: integridad y estructura de los .mat, sin usar regla_contra_matlab_modis.py
import sys, hashlib, json, numpy as np
from pathlib import Path
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8')
P = Path('..').resolve()
for f, esp in (('resultado_o2_modis.mat','d20cf7ddd3b6ba015c7b474afe627085'),('entradas_o2_modis.mat','fbe988bfa71775705daf854b50248045'),('MIROVA_VIIRS750_VRP.m','b0ceebb2b7864cd27c145dc8d41968cc')):
    h = hashlib.md5((P/f).read_bytes()).hexdigest(); print(f, h, 'OK' if h==esp else 'DISTINTO')
R = loadmat(P/'resultado_o2_modis.mat'); E = loadmat(P/'entradas_o2_modis.mat')
print('claves resultado:', [k for k in R if not k.startswith('__')])
print('claves entradas:', [k for k in E if not k.startswith('__')])
print('M13', E['M13'].shape, E['M13'].dtype, 'nan en M13:', int(np.isnan(E['M13']).sum()))
print('ALERTAS', E['ALERTAS'].shape, E['ALERTAS'].dtype)
print('BK', R['BK'].shape, 'BK[0]', R['BK'][0,0].shape, R['BK'][0,0].dtype)
print('version_matlab', R['version_matlab'])
K = E['M13'].shape[2]
# BK tienen todas 51x51 y sin NaN?
shapes = {R['BK'][k,0].shape for k in range(K)}
print('formas BK:', shapes)
nn = sum(int(np.isnan(R['BK'][k,0]).sum()) for k in range(K)); print('NaN totales en BK:', nn)
# las entradas dentro del resultado: el resultado no trae M13; LHOT permite comprobar entradas
for k in (0,1,200,403):
    a = np.asarray(E['ALERTAS'][k,0]).ravel().astype(int)
    m = E['M13'][:,:,k].astype(float)
    print(k, 'LHOT mat', float(R['LHOT'][k,0] if R['LHOT'].ndim>1 else R['LHOT'][k]), 'sum m13(a) column-major', float(m.ravel(order='F')[a-1].sum()), 'row-major', float(m.ravel(order='C')[a-1].sum()))
